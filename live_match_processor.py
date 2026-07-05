"""SignalReview hackathon live match processor powered by Alibaba Cloud Qwen.

This module is intentionally isolated from the commercial SignalReview.co backend:
- no Supabase dependency;
- no billing/auth contracts;
- no commercial artifact pipeline;
- no outcome-certainty, gambling, or staking language.

The processor accepts match context, runs four responsible-use agent passes, and returns
structured dashboard-ready JSON for a public hackathon demo.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, ValidationError

ClaimTag = Literal["data_backed", "inferred", "uncertain", "unavailable"]
ConfidenceBand = Literal["Low", "Medium", "High"]

FORBIDDEN_COPY_PATTERN = re.compile(
    r"\b(guaranteed|sure bet|fixed match|100% win|banker|free money|no[- ]?brainer|stake|staking|bookmaker|sportsbook)\b",
    re.IGNORECASE,
)

RESPONSIBLE_USE_NOTE = (
    "SignalReview provides structured sports intelligence and transparent reasoning. "
    "It does not provide betting predictions, gambling advice, bookmaker recommendations, "
    "staking instructions, certainty, guarantees, or financial advice."
)

DEFAULT_QWEN_MODEL = "qwen2.5-72b-instruct"
DEFAULT_QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


class MatchContext(BaseModel):
    match_id: str = Field(default="hackathon-demo")
    home_team: str
    away_team: str
    competition: Optional[str] = None
    kickoff_utc: Optional[str] = None
    venue: Optional[str] = None
    provider_snapshot: Dict[str, Any] = Field(default_factory=dict)
    recent_form: Dict[str, Any] = Field(default_factory=dict)
    quant_context: Dict[str, Any] = Field(default_factory=dict)
    news_context: Dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    agent_name: str
    summary: str
    dashboard_bullets: List[str] = Field(default_factory=list)
    missing_data: List[str] = Field(default_factory=list)
    claim_tags: Dict[str, ClaimTag] = Field(default_factory=dict)


class HackathonReview(BaseModel):
    match_id: str
    match: str
    competition: Optional[str]
    confidence_band: ConfidenceBand
    value_edge: str
    risk_flags: List[str]
    agents: List[AgentOutput]
    orchestrator_verdict: str
    transparency_notes: List[str]
    responsible_use_note: str = RESPONSIBLE_USE_NOTE
    raw_model: str


@dataclass(frozen=True)
class QwenSettings:
    api_key: str
    model: str = DEFAULT_QWEN_MODEL
    base_url: str = DEFAULT_QWEN_BASE_URL
    timeout_seconds: float = 45.0

    @classmethod
    def from_env(cls) -> "QwenSettings":
        api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required")
        return cls(
            api_key=api_key,
            model=os.getenv("QWEN_MODEL", DEFAULT_QWEN_MODEL).strip() or DEFAULT_QWEN_MODEL,
            base_url=normalize_qwen_base_url(os.getenv("QWEN_BASE_URL", DEFAULT_QWEN_BASE_URL)),
            timeout_seconds=float(os.getenv("QWEN_TIMEOUT_SECONDS", "45")),
        )

    def redacted(self) -> Dict[str, Any]:
        parsed = urlparse(self.base_url)
        return {
            "model": self.model,
            "base_url": self.base_url,
            "host": parsed.netloc,
            "has_api_key": bool(self.api_key),
            "api_key_prefix": self.api_key[:4] + "..." if self.api_key else "missing",
            "timeout_seconds": self.timeout_seconds,
        }


def normalize_qwen_base_url(raw: str) -> str:
    value = (raw or DEFAULT_QWEN_BASE_URL).strip().rstrip("/")
    if value.endswith("/chat/completions"):
        value = value[: -len("/chat/completions")]
    return value


def qwen_runtime_diagnostics() -> Dict[str, Any]:
    try:
        settings = QwenSettings.from_env()
        return {"status": "configured", **settings.redacted()}
    except Exception as exc:  # noqa: BLE001 - diagnostic endpoint must stay resilient.
        return {"status": "misconfigured", "error": str(exc)}


class QwenCloudClient:
    def __init__(self, settings: QwenSettings):
        self.settings = settings

    async def chat_json(self, messages: List[Dict[str, str]], *, temperature: float = 0.2) -> Dict[str, Any]:
        url = f"{self.settings.base_url}/chat/completions"
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
        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 403:
                raise RuntimeError(self._format_403(url, response.text))
            if response.status_code == 401:
                raise RuntimeError(self._format_401(url, response.text))
            response.raise_for_status()
            data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Qwen returned non-JSON content: {content[:500]}") from exc

    def _format_403(self, url: str, body: str) -> str:
        return (
            "Qwen endpoint returned 403 Forbidden. FastAPI is healthy, but Alibaba rejected the request. "
            f"Checked url={url}; model={self.settings.model}; host={urlparse(self.settings.base_url).netloc}. "
            "Most likely causes: API key is not authorized for this workspace endpoint, model name is not enabled in this region/workspace, "
            "or QWEN_BASE_URL points to a MaaS workspace that requires a different key. "
            f"Provider body preview={body[:300]}"
        )

    def _format_401(self, url: str, body: str) -> str:
        return (
            "Qwen endpoint returned 401 Unauthorized. Verify DASHSCOPE_API_KEY and that the key is exported into the systemd service env. "
            f"Checked url={url}; model={self.settings.model}; provider body preview={body[:300]}"
        )


class LiveMatchProcessor:
    def __init__(self, qwen: QwenCloudClient):
        self.qwen = qwen

    async def review_match(self, context: MatchContext) -> HackathonReview:
        prompt = self._build_prompt(context)
        model_json = await self.qwen.chat_json(prompt)
        sanitized = self._sanitize_model_json(model_json, context)
        try:
            return HackathonReview.model_validate(sanitized)
        except ValidationError as exc:
            raise RuntimeError(f"Invalid Qwen review schema: {exc}") from exc

    def _build_prompt(self, context: MatchContext) -> List[Dict[str, str]]:
        system = (
            "You are SignalReview Hackathon Qwen Agent Runtime. Produce dashboard-ready JSON only. "
            "You must not invent odds, injuries, private news, ROI, win-rate, model accuracy, lambda, or outcomes. "
            "Use claim tags only: data_backed, inferred, uncertain, unavailable. "
            "Never use gambling certainty or bookmaker language. Keep missing data visible."
        )
        schema = {
            "match_id": context.match_id,
            "match": f"{context.home_team} vs {context.away_team}",
            "competition": context.competition,
            "confidence_band": "Low|Medium|High",
            "value_edge": "string, responsible-use scenario label, not betting advice",
            "risk_flags": ["array of concise risk labels"],
            "agents": [
                {
                    "agent_name": "Statistician|Skeptic|Upside Scout|Orchestrator",
                    "summary": "string",
                    "dashboard_bullets": ["string"],
                    "missing_data": ["string"],
                    "claim_tags": {"claim_name": "data_backed|inferred|uncertain|unavailable"},
                }
            ],
            "orchestrator_verdict": "string",
            "transparency_notes": ["string"],
            "responsible_use_note": RESPONSIBLE_USE_NOTE,
            "raw_model": os.getenv("QWEN_MODEL", DEFAULT_QWEN_MODEL),
        }
        user = {
            "task": "Run Statistician, Skeptic, Upside Scout, and Orchestrator review for this match context.",
            "required_schema": schema,
            "match_context": context.model_dump(),
        }
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ]

    def _sanitize_model_json(self, model_json: Dict[str, Any], context: MatchContext) -> Dict[str, Any]:
        data = dict(model_json)
        data["match_id"] = context.match_id
        data["match"] = f"{context.home_team} vs {context.away_team}"
        data["competition"] = context.competition
        data["responsible_use_note"] = RESPONSIBLE_USE_NOTE
        data["raw_model"] = os.getenv("QWEN_MODEL", DEFAULT_QWEN_MODEL)
        data["confidence_band"] = self._safe_confidence(data.get("confidence_band"))
        data["value_edge"] = self._clean_text(str(data.get("value_edge") or "Scenario review only"))
        data["orchestrator_verdict"] = self._clean_text(
            str(data.get("orchestrator_verdict") or "Insufficient verified evidence for a stronger verdict.")
        )
        data["risk_flags"] = [self._clean_text(str(item)) for item in data.get("risk_flags", []) if str(item).strip()]
        data["transparency_notes"] = [
            self._clean_text(str(item)) for item in data.get("transparency_notes", []) if str(item).strip()
        ] or ["Unavailable provider fields are preserved as missing data, not filled by the model."]
        data["agents"] = self._safe_agents(data.get("agents"))
        return data

    def _safe_agents(self, agents: Any) -> List[Dict[str, Any]]:
        if not isinstance(agents, list):
            agents = []
        cleaned: List[Dict[str, Any]] = []
        for raw in agents[:4]:
            if not isinstance(raw, dict):
                continue
            claim_tags = raw.get("claim_tags") if isinstance(raw.get("claim_tags"), dict) else {}
            cleaned.append(
                {
                    "agent_name": self._clean_text(str(raw.get("agent_name") or "Agent")),
                    "summary": self._clean_text(str(raw.get("summary") or "No summary returned.")),
                    "dashboard_bullets": [
                        self._clean_text(str(item)) for item in raw.get("dashboard_bullets", []) if str(item).strip()
                    ],
                    "missing_data": [
                        self._clean_text(str(item)) for item in raw.get("missing_data", []) if str(item).strip()
                    ],
                    "claim_tags": {
                        self._clean_text(str(key)): self._safe_claim_tag(value) for key, value in claim_tags.items()
                    },
                }
            )
        if cleaned:
            return cleaned
        return [
            {
                "agent_name": "Orchestrator",
                "summary": "Qwen returned no agent breakdown; verified inputs remain limited.",
                "dashboard_bullets": ["Missing agent detail is exposed as a transparency note."],
                "missing_data": ["agent_breakdown"],
                "claim_tags": {"agent_breakdown": "unavailable"},
            }
        ]

    @staticmethod
    def _safe_confidence(value: Any) -> ConfidenceBand:
        normalized = str(value or "Low").strip().lower()
        if normalized == "high":
            return "High"
        if normalized == "medium":
            return "Medium"
        return "Low"

    @staticmethod
    def _safe_claim_tag(value: Any) -> ClaimTag:
        normalized = str(value or "unavailable").strip().lower()
        if normalized in {"data_backed", "inferred", "uncertain", "unavailable"}:
            return normalized  # type: ignore[return-value]
        return "unavailable"

    @staticmethod
    def _clean_text(value: str) -> str:
        value = FORBIDDEN_COPY_PATTERN.sub("decision-support", value)
        return " ".join(value.split())


def build_processor_from_env() -> LiveMatchProcessor:
    return LiveMatchProcessor(QwenCloudClient(QwenSettings.from_env()))
