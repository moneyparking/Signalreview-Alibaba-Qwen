"""Secure four-agent SignalReview runtime for the public Alibaba Qwen repository.

This module contains only the public hackathon debate contract. It has no Supabase,
authentication, billing, subscription, private calibration-table, or commercial
artifact-pipeline dependency.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Sequence
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, ValidationError

from forensic_data_broker import ForensicDataBroker

ClaimTag = Literal["data_backed", "inferred", "uncertain", "unavailable"]
ConfidenceBand = Literal["Low", "Medium", "High"]
ReasoningStatus = Literal["ready", "fallback"]

CLAIM_TAGS = {"data_backed", "inferred", "uncertain", "unavailable"}
FORBIDDEN_COPY_PATTERN = re.compile(
    r"\b(?:guaranteed|guarantee|sure[ -]?bet|fixed[ -]?match|100%[ -]?win|banker|free[ -]?money|"
    r"no[ -]?brainer|stake|staking|bookmaker|sportsbook|wager|betting[ -]?pick|lock[ -]?of[ -]?the[ -]?day|roi)\b",
    re.IGNORECASE,
)
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z_])[+-]?\d+(?:\.\d+)?%?(?![A-Za-z_])")
RAW_ID_PATTERN = re.compile(r"\b(?:idx|index|qp|kpi|feature|metric|row|claim)[-_:.][A-Za-z0-9_.:-]+\b", re.IGNORECASE)

RESPONSIBLE_USE_NOTE = (
    "SignalReview provides structured sports intelligence and transparent reasoning. "
    "It does not provide betting predictions, gambling advice, bookmaker recommendations, "
    "staking instructions, certainty, guarantees, or financial advice."
)

COMMON_SYSTEM_CONTRACT = "\n".join(
    (
        "Return one JSON object only; never return Markdown or prose outside JSON.",
        "Use only evidence supplied in the forensic packet. Never invent odds, injuries, line movement, private news, ROI, accuracy, lambdas, or outcomes.",
        "Allowed claim tags are data_backed, inferred, uncertain, unavailable.",
        "Every number in debate text must exactly duplicate a value from a structured ref attached to that claim; never round, rescale, derive, or convert it.",
        "Raw evidence refs and claim IDs belong only in structured fields. Never print them inside summaries, bullets, claim text, verdict text, or risk labels.",
        "Golden Dataset rows are non-live calibration context. They can preserve or lower confidence and can never be described as live evidence or outcome accuracy.",
        "Missing evidence constrains confidence; it is never negative outcome evidence.",
        "Never use gambling, certainty, bookmaker, staking, guaranteed-outcome, or fake-performance language.",
    )
)


class RuntimeConfigurationError(RuntimeError):
    """Raised when required Vercel/Qwen runtime settings are missing or invalid."""


class AgentContractError(RuntimeError):
    """Raised when a model response violates the public debate contract."""


class MatchContext(BaseModel):
    match_id: str = Field(default="hackathon-demo")
    home_team: str = Field(min_length=1, max_length=120)
    away_team: str = Field(min_length=1, max_length=120)
    competition: Optional[str] = Field(default=None, max_length=160)
    kickoff_utc: Optional[str] = Field(default=None, max_length=64)
    venue: Optional[str] = Field(default=None, max_length=160)
    provider_snapshot: Dict[str, Any] = Field(default_factory=dict)
    recent_form: Dict[str, Any] = Field(default_factory=dict)
    quant_context: Dict[str, Any] = Field(default_factory=dict)
    news_context: Dict[str, Any] = Field(default_factory=dict)
    golden_dataset: Dict[str, Any] = Field(default_factory=dict)


class EvidenceClaim(BaseModel):
    claim_id: str
    text: str
    refs: List[str] = Field(default_factory=list)
    claim_tag: ClaimTag
    challenges_claim_id: Optional[str] = None


class AgentOutput(BaseModel):
    agent_name: str
    summary: str
    claims: List[EvidenceClaim] = Field(default_factory=list)
    dashboard_bullets: List[str] = Field(default_factory=list)
    missing_data: List[str] = Field(default_factory=list)
    claim_tags: Dict[str, ClaimTag] = Field(default_factory=dict)


class OrchestratorDecision(BaseModel):
    confidence_band: ConfidenceBand
    value_edge: str
    risk_flags: List[str] = Field(default_factory=list)
    accepted_claim_ids: List[str] = Field(default_factory=list)
    rejected_claim_ids: List[str] = Field(default_factory=list)
    unresolved_claim_ids: List[str] = Field(default_factory=list)
    decisive_invalidation_claim_id: Optional[str] = None


class HackathonReview(BaseModel):
    match_id: str
    match: str
    competition: Optional[str]
    confidence_band: ConfidenceBand
    value_edge: str
    risk_flags: List[str]
    agents: List[AgentOutput]
    orchestrator_verdict: str
    orchestrator_decision: OrchestratorDecision
    transparency_notes: List[str]
    responsible_use_note: str = RESPONSIBLE_USE_NOTE
    reasoning_status: ReasoningStatus
    reasoning_diagnostic: Dict[str, Any] = Field(default_factory=dict)
    broker_diagnostics: Dict[str, Any] = Field(default_factory=dict)
    debate_contract: Dict[str, Any] = Field(default_factory=dict)
    raw_model: str


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeConfigurationError(f"{name} is required")
    return value


def _positive_int_env(name: str, *, allow_zero: bool = False) -> int:
    raw = _required_env(name)
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeConfigurationError(f"{name} must be an integer") from exc
    minimum = 0 if allow_zero else 1
    if value < minimum:
        raise RuntimeConfigurationError(f"{name} must be >= {minimum}")
    return value


def normalize_qwen_base_url(raw: str) -> str:
    value = raw.strip().rstrip("/")
    if value.endswith("/chat/completions"):
        value = value[: -len("/chat/completions")]
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeConfigurationError("QWEN_BASE_URL must be an absolute HTTPS URL")
    return value


@dataclass(frozen=True)
class QwenSettings:
    api_key: str
    model: str
    base_url: str
    timeout_ms: int
    total_timeout_ms: int
    max_repair_attempts: int
    provider: str

    @classmethod
    def from_env(cls) -> "QwenSettings":
        provider = _required_env("SIGNALREVIEW_REASONING_PROVIDER").lower()
        if provider != "qwen":
            raise RuntimeConfigurationError("SIGNALREVIEW_REASONING_PROVIDER must be qwen")
        timeout_ms = _positive_int_env("QWEN_TIMEOUT_MS")
        total_timeout_ms = _positive_int_env("QWEN_TOTAL_TIMEOUT_MS")
        if total_timeout_ms < timeout_ms:
            raise RuntimeConfigurationError("QWEN_TOTAL_TIMEOUT_MS must be >= QWEN_TIMEOUT_MS")
        repair_attempts = _positive_int_env("QWEN_MAX_REPAIR_ATTEMPTS", allow_zero=True)
        if repair_attempts > 4:
            raise RuntimeConfigurationError("QWEN_MAX_REPAIR_ATTEMPTS must be <= 4")
        return cls(
            api_key=_required_env("QWEN_API_KEY"),
            model=_required_env("QWEN_MODEL"),
            base_url=normalize_qwen_base_url(_required_env("QWEN_BASE_URL")),
            timeout_ms=timeout_ms,
            total_timeout_ms=total_timeout_ms,
            max_repair_attempts=repair_attempts,
            provider=provider,
        )

    def public_diagnostics(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model_configured": bool(self.model),
            "base_url_configured": bool(self.base_url),
            "api_key_configured": bool(self.api_key),
            "timeout_configured": self.timeout_ms > 0 and self.total_timeout_ms > 0,
            "repair_policy_configured": self.max_repair_attempts >= 0,
        }


def qwen_runtime_diagnostics() -> Dict[str, Any]:
    try:
        settings = QwenSettings.from_env()
        return {"status": "configured", **settings.public_diagnostics()}
    except RuntimeConfigurationError as exc:
        return {"status": "misconfigured", "error": str(exc)}


async def qwen_models_probe() -> Dict[str, Any]:
    try:
        settings = QwenSettings.from_env()
    except RuntimeConfigurationError as exc:
        return {"status": "misconfigured", "error": str(exc)}

    try:
        async with httpx.AsyncClient(timeout=settings.timeout_ms / 1000) as client:
            response = await client.get(
                f"{settings.base_url}/models",
                headers={"Authorization": f"Bearer {settings.api_key}"},
            )
        payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        models = payload.get("data", []) if isinstance(payload, Mapping) else []
        visible = any(isinstance(item, Mapping) and item.get("id") == settings.model for item in models)
        return {
            "status": "ok" if response.is_success else "provider_error",
            "http_status": response.status_code,
            "configured_model_visible": visible,
            "visible_model_count": len(models) if isinstance(models, list) else 0,
        }
    except (httpx.HTTPError, ValueError, TypeError):
        return {"status": "request_failed"}


class QwenCloudClient:
    def __init__(self, settings: QwenSettings):
        self.settings = settings

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        *,
        timeout_seconds: float,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        return _parse_json_object(content)


def _parse_json_object(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    text = str(value or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise AgentContractError("model output is not a JSON object")
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise AgentContractError("model output is not valid JSON") from exc
    if not isinstance(parsed, Mapping):
        raise AgentContractError("model output must be a JSON object")
    return dict(parsed)


def _clean_text(value: Any, *, max_length: int = 600) -> str:
    text = " ".join(str(value or "").split())[:max_length]
    return FORBIDDEN_COPY_PATTERN.sub("decision-support", text)


def _row_map(packet: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = packet.get("rows", [])
    return {
        str(row.get("ref")): dict(row)
        for row in rows
        if isinstance(row, Mapping) and str(row.get("ref") or "")
    }


def _text_fields(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"refs", "claim_id", "challenges_claim_id", "accepted_claim_ids", "rejected_claim_ids", "unresolved_claim_ids", "decisive_invalidation_claim_id"}:
                continue
            yield from _text_fields(item)
    elif isinstance(value, list):
        for item in value:
            yield from _text_fields(item)


def _numeric_values_for_refs(refs: Sequence[str], rows: Mapping[str, Mapping[str, Any]]) -> List[float]:
    values: List[float] = []
    for ref in refs:
        row = rows.get(ref)
        if not row:
            continue
        value = row.get("value")
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            values.append(float(value))
    return values


def _numbers_are_grounded(text: str, refs: Sequence[str], rows: Mapping[str, Mapping[str, Any]]) -> bool:
    candidates = _numeric_values_for_refs(refs, rows)
    for token in NUMBER_PATTERN.findall(text):
        normalized = token.rstrip("%")
        try:
            number = float(normalized)
        except ValueError:
            return False
        if not any(math.isclose(number, candidate, rel_tol=0.0, abs_tol=max(1e-12, abs(candidate) * 1e-12)) for candidate in candidates):
            return False
    return True


def _assert_public_text(value: Any, packet: Mapping[str, Any]) -> None:
    refs = [str(ref) for ref in packet.get("canonical_refs", [])]
    for text in _text_fields(value):
        if FORBIDDEN_COPY_PATTERN.search(text):
            raise AgentContractError("forbidden public lexicon")
        if RAW_ID_PATTERN.search(text):
            raise AgentContractError("raw identifier leaked into public text")
        lowered = text.lower()
        if any(ref and ref.lower() in lowered for ref in refs):
            raise AgentContractError("structured evidence ref leaked into public text")


def _normalize_claim(raw: Mapping[str, Any]) -> EvidenceClaim:
    return EvidenceClaim(
        claim_id=str(raw.get("claim_id") or "").strip(),
        text=_clean_text(raw.get("text")),
        refs=[str(item).strip() for item in raw.get("refs", []) if str(item).strip()][:3],
        claim_tag=str(raw.get("claim_tag") or "unavailable").strip().lower(),
        challenges_claim_id=(str(raw.get("challenges_claim_id")).strip() if raw.get("challenges_claim_id") else None),
    )


def _normalize_agent(name: str, payload: Mapping[str, Any]) -> AgentOutput:
    claims = [_normalize_claim(item) for item in payload.get("claims", []) if isinstance(item, Mapping)]
    return AgentOutput(
        agent_name=name,
        summary=_clean_text(payload.get("summary") or "Evidence remains bounded by the supplied packet."),
        claims=claims,
        dashboard_bullets=[_clean_text(item, max_length=240) for item in payload.get("dashboard_bullets", []) if str(item).strip()][:5],
        missing_data=[_clean_text(item, max_length=120) for item in payload.get("missing_data", []) if str(item).strip()][:10],
        claim_tags={claim.claim_id: claim.claim_tag for claim in claims},
    )


def _validate_agent(
    agent: AgentOutput,
    *,
    packet: Mapping[str, Any],
    expected_ids: Sequence[str],
    statistician: Optional[AgentOutput] = None,
) -> None:
    rows = _row_map(packet)
    canonical_refs = set(rows)
    actual_ids = [claim.claim_id for claim in agent.claims]
    if actual_ids != list(expected_ids):
        raise AgentContractError(f"{agent.agent_name} claim ids must be {list(expected_ids)}")
    if not agent.summary:
        raise AgentContractError(f"{agent.agent_name} summary is required")
    for claim in agent.claims:
        if not claim.text:
            raise AgentContractError(f"{claim.claim_id} text is required")
        if claim.claim_tag not in CLAIM_TAGS:
            raise AgentContractError(f"{claim.claim_id} claim tag is invalid")
        if rows and not claim.refs:
            raise AgentContractError(f"{claim.claim_id} requires a structured evidence ref")
        if any(ref not in canonical_refs for ref in claim.refs):
            raise AgentContractError(f"{claim.claim_id} uses a non-canonical ref")
        if not _numbers_are_grounded(claim.text, claim.refs, rows):
            raise AgentContractError(f"{claim.claim_id} contains an ungrounded number")
    if statistician is not None:
        statistician_by_id = {claim.claim_id: claim for claim in statistician.claims}
        for index, claim in enumerate(agent.claims, start=1):
            expected_stat_id = f"S{index}"
            if claim.challenges_claim_id != expected_stat_id:
                raise AgentContractError(f"{claim.claim_id} must challenge {expected_stat_id}")
            paired = statistician_by_id[expected_stat_id]
            if not set(claim.refs).intersection(paired.refs):
                raise AgentContractError(f"{claim.claim_id} must cite the same index as {expected_stat_id}")
    _assert_public_text(agent.model_dump(), packet)


def _normalize_orchestrator(payload: Mapping[str, Any], packet: Mapping[str, Any]) -> tuple[AgentOutput, OrchestratorDecision]:
    agent = _normalize_agent("Orchestrator", payload)
    confidence = str(payload.get("confidence_band") or "Low").strip().title()
    if confidence not in {"Low", "Medium", "High"}:
        confidence = "Low"
    decision = OrchestratorDecision(
        confidence_band=confidence,
        value_edge=_clean_text(payload.get("value_edge") or "No verified value-edge signal"),
        risk_flags=[_clean_text(item, max_length=120) for item in payload.get("risk_flags", []) if str(item).strip()][:8],
        accepted_claim_ids=[str(item) for item in payload.get("accepted_claim_ids", []) if str(item).strip()],
        rejected_claim_ids=[str(item) for item in payload.get("rejected_claim_ids", []) if str(item).strip()],
        unresolved_claim_ids=[str(item) for item in payload.get("unresolved_claim_ids", []) if str(item).strip()],
        decisive_invalidation_claim_id=(
            str(payload.get("decisive_invalidation_claim_id")) if payload.get("decisive_invalidation_claim_id") else None
        ),
    )
    _validate_agent(agent, packet=packet, expected_ids=("O1", "O2"))
    all_specialist_ids = {"S1", "S2", "S3", "K1", "K2", "K3", "U1", "U2", "U3"}
    classified = decision.accepted_claim_ids + decision.rejected_claim_ids + decision.unresolved_claim_ids
    if set(classified) != all_specialist_ids or len(classified) != len(set(classified)):
        raise AgentContractError("Orchestrator must classify every specialist claim exactly once")
    if decision.decisive_invalidation_claim_id not in {"S3", "K3", "U3", None}:
        raise AgentContractError("Orchestrator decisive invalidation must reference S3, K3, or U3")
    _assert_public_text(decision.model_dump(), packet)
    return agent, decision


def _role_schema(role: str) -> Dict[str, Any]:
    base_claim = {
        "claim_id": "fixed role claim id",
        "text": "public text; exact values only; no raw ids",
        "refs": ["one to three canonical refs from packet.rows[*].ref"],
        "claim_tag": "data_backed|inferred|uncertain|unavailable",
    }
    if role == "Statistician":
        return {
            "summary": "concise evidence synthesis",
            "claims": [{**base_claim, "claim_id": claim_id} for claim_id in ("S1", "S2", "S3")],
            "dashboard_bullets": ["concise public bullet"],
            "missing_data": ["missing domain label"],
        }
    if role == "Skeptic":
        return {
            "summary": "concise adversarial synthesis",
            "claims": [
                {**base_claim, "claim_id": f"K{index}", "challenges_claim_id": f"S{index}"}
                for index in range(1, 4)
            ],
            "dashboard_bullets": ["concise public bullet"],
            "missing_data": ["missing domain label"],
        }
    if role == "Upside Scout":
        return {
            "summary": "bounded scenario synthesis",
            "claims": [{**base_claim, "claim_id": claim_id} for claim_id in ("U1", "U2", "U3")],
            "dashboard_bullets": ["concise public bullet"],
            "missing_data": ["missing domain label"],
        }
    return {
        "summary": "adjudication summary",
        "claims": [{**base_claim, "claim_id": claim_id} for claim_id in ("O1", "O2")],
        "dashboard_bullets": ["concise public bullet"],
        "missing_data": ["missing domain label"],
        "confidence_band": "Low|Medium|High",
        "value_edge": "responsible-use scenario label; never a recommendation",
        "risk_flags": ["concise risk label"],
        "accepted_claim_ids": ["specialist ids"],
        "rejected_claim_ids": ["specialist ids"],
        "unresolved_claim_ids": ["specialist ids"],
        "decisive_invalidation_claim_id": "S3|K3|U3|null",
    }


def _role_instruction(role: str) -> str:
    if role == "Statistician":
        return (
            "Act as Statistician. Produce S1, S2, and S3 in that order. Each claim must cite a calculated or observed row and repeat its exact value with the public metric label. "
            "S1 is the strongest driver, S2 is the strongest counter-signal, and S3 is the invalidation condition."
        )
    if role == "Skeptic":
        return (
            "Act as Skeptic. Produce K1, K2, and K3 in that order. K1 must challenge S1 through at least one identical ref and exact value; K2 must do the same for S2; K3 must do the same for S3. "
            "Challenge confidence, sample depth, missing domains, and false precision without inventing negative evidence."
        )
    if role == "Upside Scout":
        return (
            "Act as Upside Scout. Produce U1 primary scenario, U2 alternate scenario, and U3 observable invalidation. Treat tactical upside as inferred unless directly supported. "
            "Do not collapse scenarios into certainty or recommendations."
        )
    return (
        "Act as Orchestrator. Produce O1 evidence-bound verdict and O2 decisive invalidation. Classify every S, K, and U claim exactly once as accepted, rejected, or unresolved. "
        "Preserve the Skeptic ceiling, apply Golden Dataset only as non-live calibration, and never upgrade missing or inferred evidence."
    )


def _build_messages(
    role: str,
    packet: Mapping[str, Any],
    prior_agents: Sequence[AgentOutput],
    *,
    repair_diagnostic: Optional[str] = None,
) -> List[Dict[str, str]]:
    prior = [agent.model_dump() for agent in prior_agents]
    user = {
        "role": role,
        "required_schema": _role_schema(role),
        "forensic_evidence_packet": packet,
        "prior_agent_outputs": prior,
        "repair_diagnostic": repair_diagnostic,
        "publication_rule": "raw refs remain in refs arrays only; public text uses labels and exact grounded values",
    }
    system = f"{COMMON_SYSTEM_CONTRACT}\n{_role_instruction(role)}"
    if repair_diagnostic:
        system += (
            "\nPrevious output failed validation. Rewrite the complete role object, not a patch. "
            f"Validation diagnostic: {repair_diagnostic}."
        )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False, separators=(",", ":"))},
    ]


def _format_value(row: Mapping[str, Any]) -> str:
    value = row.get("value")
    if isinstance(value, float) and value.is_integer():
        rendered = str(int(value))
    else:
        rendered = str(value)
    unit = row.get("unit")
    return f"{rendered}{unit or ''}"


def _fallback_agents(packet: Mapping[str, Any]) -> tuple[List[AgentOutput], OrchestratorDecision]:
    rows = list(_row_map(packet).values())[:3]
    missing = [str(item) for item in packet.get("missing_domains", [])]
    while len(rows) < 3:
        rows.append({})

    statistician_claims: List[EvidenceClaim] = []
    skeptic_claims: List[EvidenceClaim] = []
    for index, row in enumerate(rows, start=1):
        if row:
            label = _clean_text(row.get("label"), max_length=120)
            value = _format_value(row)
            ref = str(row["ref"])
            statistician_text = f"{label} is recorded at {value}; interpretation remains bounded by supplied evidence."
            skeptic_text = f"{label} at {value} cannot remove uncertainty from missing or non-live domains."
            refs = [ref]
            tag: ClaimTag = "data_backed"
        else:
            statistician_text = "No additional calculated metric is available for this evidence position."
            skeptic_text = "The unavailable evidence position prevents a stronger confidence claim."
            refs = []
            tag = "unavailable"
        statistician_claims.append(
            EvidenceClaim(claim_id=f"S{index}", text=statistician_text, refs=refs, claim_tag=tag)
        )
        skeptic_claims.append(
            EvidenceClaim(
                claim_id=f"K{index}",
                text=skeptic_text,
                refs=refs,
                claim_tag="uncertain" if refs else "unavailable",
                challenges_claim_id=f"S{index}",
            )
        )

    statistician = AgentOutput(
        agent_name="Statistician",
        summary="Deterministic recovery published only the request-grounded evidence available to the broker.",
        claims=statistician_claims,
        dashboard_bullets=[claim.text for claim in statistician_claims],
        missing_data=missing,
        claim_tags={claim.claim_id: claim.claim_tag for claim in statistician_claims},
    )
    skeptic = AgentOutput(
        agent_name="Skeptic",
        summary="Each quantitative position remains constrained by missing evidence and non-live calibration boundaries.",
        claims=skeptic_claims,
        dashboard_bullets=[claim.text for claim in skeptic_claims],
        missing_data=missing,
        claim_tags={claim.claim_id: claim.claim_tag for claim in skeptic_claims},
    )
    scout_claims = [
        EvidenceClaim(
            claim_id="U1",
            text="Primary scenario remains plausible only where observed provider context and deterministic metrics align.",
            refs=[str(rows[0]["ref"])] if rows[0] else [],
            claim_tag="inferred" if rows[0] else "unavailable",
        ),
        EvidenceClaim(
            claim_id="U2",
            text="Alternate scenario remains open because missing domains cannot be converted into directional evidence.",
            refs=[str(rows[1]["ref"])] if rows[1] else [],
            claim_tag="uncertain" if rows[1] else "unavailable",
        ),
        EvidenceClaim(
            claim_id="U3",
            text="Scenario confidence should fall when new verified evidence conflicts with the current packet.",
            refs=[str(rows[2]["ref"])] if rows[2] else [],
            claim_tag="inferred" if rows[2] else "unavailable",
        ),
    ]
    scout = AgentOutput(
        agent_name="Upside Scout",
        summary="Scenario upside is retained as a bounded hypothesis rather than an outcome assertion.",
        claims=scout_claims,
        dashboard_bullets=[claim.text for claim in scout_claims],
        missing_data=missing,
        claim_tags={claim.claim_id: claim.claim_tag for claim in scout_claims},
    )
    orchestrator_claims = [
        EvidenceClaim(
            claim_id="O1",
            text="The evidence supports a constrained review, while missing domains prevent a high-confidence conclusion.",
            refs=[str(rows[0]["ref"])] if rows[0] else [],
            claim_tag="uncertain" if rows[0] else "unavailable",
        ),
        EvidenceClaim(
            claim_id="O2",
            text="Any material conflict from newly verified evidence invalidates the current scenario hierarchy.",
            refs=[str(rows[2]["ref"])] if rows[2] else [],
            claim_tag="inferred" if rows[2] else "unavailable",
        ),
    ]
    orchestrator = AgentOutput(
        agent_name="Orchestrator",
        summary="The four-role rail completed through deterministic contract-safe recovery.",
        claims=orchestrator_claims,
        dashboard_bullets=[claim.text for claim in orchestrator_claims],
        missing_data=missing,
        claim_tags={claim.claim_id: claim.claim_tag for claim in orchestrator_claims},
    )
    evidence_count = sum(1 for row in rows if row)
    confidence: ConfidenceBand = "Medium" if evidence_count >= 3 and not missing else "Low"
    decision = OrchestratorDecision(
        confidence_band=confidence,
        value_edge="No verified value-edge signal",
        risk_flags=["Incomplete evidence coverage"] if missing else ["Model interpretation remains non-certain"],
        accepted_claim_ids=["S1"] if evidence_count else [],
        rejected_claim_ids=[],
        unresolved_claim_ids=[
            claim_id for claim_id in ("S1", "S2", "S3", "K1", "K2", "K3", "U1", "U2", "U3")
            if claim_id != "S1" or not evidence_count
        ],
        decisive_invalidation_claim_id="K3",
    )
    return [statistician, skeptic, scout, orchestrator], decision


class LiveMatchProcessor:
    def __init__(self, qwen: QwenCloudClient, broker: Optional[ForensicDataBroker] = None):
        self.qwen = qwen
        self.broker = broker or ForensicDataBroker()

    async def _run_role(
        self,
        role: str,
        packet: Mapping[str, Any],
        prior_agents: Sequence[AgentOutput],
        *,
        deadline: float,
        statistician: Optional[AgentOutput] = None,
    ) -> tuple[AgentOutput, Optional[OrchestratorDecision]]:
        diagnostic: Optional[str] = None
        for attempt in range(self.qwen.settings.max_repair_attempts + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("total reasoning deadline exceeded")
            timeout_seconds = min(self.qwen.settings.timeout_ms / 1000, remaining)
            payload = await self.qwen.chat_json(
                _build_messages(role, packet, prior_agents, repair_diagnostic=diagnostic),
                timeout_seconds=timeout_seconds,
            )
            try:
                if role == "Orchestrator":
                    agent, decision = _normalize_orchestrator(payload, packet)
                    return agent, decision
                agent = _normalize_agent(role, payload)
                expected = {
                    "Statistician": ("S1", "S2", "S3"),
                    "Skeptic": ("K1", "K2", "K3"),
                    "Upside Scout": ("U1", "U2", "U3"),
                }[role]
                _validate_agent(
                    agent,
                    packet=packet,
                    expected_ids=expected,
                    statistician=statistician if role == "Skeptic" else None,
                )
                return agent, None
            except (AgentContractError, ValidationError) as exc:
                diagnostic = _clean_text(str(exc), max_length=240)
                if attempt >= self.qwen.settings.max_repair_attempts:
                    raise AgentContractError(diagnostic) from exc
        raise AgentContractError("role validation exhausted")

    async def review_match(self, context: MatchContext) -> HackathonReview:
        packet = self.broker.build(context.model_dump())
        deadline = time.monotonic() + self.qwen.settings.total_timeout_ms / 1000
        agents: List[AgentOutput]
        decision: OrchestratorDecision
        reasoning_status: ReasoningStatus = "ready"
        diagnostic: Dict[str, Any] = {"status": "validated_four_agent_qwen"}
        try:
            statistician, _ = await self._run_role("Statistician", packet, [], deadline=deadline)
            skeptic, _ = await self._run_role(
                "Skeptic", packet, [statistician], deadline=deadline, statistician=statistician
            )
            scout, _ = await self._run_role(
                "Upside Scout", packet, [statistician, skeptic], deadline=deadline
            )
            orchestrator, decision_or_none = await self._run_role(
                "Orchestrator", packet, [statistician, skeptic, scout], deadline=deadline
            )
            if decision_or_none is None:
                raise AgentContractError("orchestrator decision missing")
            decision = decision_or_none
            agents = [statistician, skeptic, scout, orchestrator]
        except (AgentContractError, ValidationError, httpx.HTTPError, TimeoutError, asyncio.TimeoutError, ValueError, TypeError) as exc:
            agents, decision = _fallback_agents(packet)
            reasoning_status = "fallback"
            diagnostic = {
                "status": "deterministic_contract_recovery",
                "error_type": type(exc).__name__,
                "detail": "Qwen output or transport did not satisfy the bounded public contract.",
            }

        orchestrator = agents[-1]
        verdict = orchestrator.claims[0].text if orchestrator.claims else orchestrator.summary
        transparency_notes = [
            "The forensic broker reused request-supplied evidence and performed zero provider network calls.",
            "Raw evidence identifiers remain in structured refs and are removed from public debate text.",
            "Golden Dataset context is non-live calibration and cannot establish outcome accuracy.",
        ]
        if packet.get("missing_domains"):
            transparency_notes.append(
                "Unavailable domains remain visible and can only reduce confidence: "
                + ", ".join(str(item) for item in packet["missing_domains"])
                + "."
            )
        return HackathonReview(
            match_id=context.match_id,
            match=f"{context.home_team} vs {context.away_team}",
            competition=context.competition,
            confidence_band=decision.confidence_band,
            value_edge=decision.value_edge,
            risk_flags=decision.risk_flags,
            agents=agents,
            orchestrator_verdict=verdict,
            orchestrator_decision=decision,
            transparency_notes=transparency_notes,
            responsible_use_note=RESPONSIBLE_USE_NOTE,
            reasoning_status=reasoning_status,
            reasoning_diagnostic=diagnostic,
            broker_diagnostics=dict(packet.get("diagnostics", {})),
            debate_contract={
                "schema_version": "signalreview.public_four_agent_debate.v1",
                "agent_order": ["Statistician", "Skeptic", "Upside Scout", "Orchestrator"],
                "skeptic_pairing": {"K1": "S1", "K2": "S2", "K3": "S3"},
                "raw_ids_hidden_from_public_text": True,
                "golden_dataset_grounding": packet.get("golden_dataset_status"),
                "gambling_lexicon_blocked": True,
            },
            raw_model=self.qwen.settings.model,
        )


def build_processor_from_env() -> LiveMatchProcessor:
    settings = QwenSettings.from_env()
    return LiveMatchProcessor(QwenCloudClient(settings))


__all__ = [
    "AgentOutput",
    "HackathonReview",
    "LiveMatchProcessor",
    "MatchContext",
    "QwenCloudClient",
    "QwenSettings",
    "RuntimeConfigurationError",
    "build_processor_from_env",
    "qwen_models_probe",
    "qwen_runtime_diagnostics",
]
