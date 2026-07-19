#!/usr/bin/env python3
"""Run public-safe end-to-end verification against the deployed Alibaba judge runtime."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

EXPECTED_AGENTS = ["Statistician", "Skeptic", "Upside Scout", "Orchestrator"]


class VerificationError(RuntimeError):
    pass


def record(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def list_of_records(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: Mapping[str, Any] | None = None,
    timeout: float = 180.0,
) -> tuple[dict[str, Any], float]:
    body = None if payload is None else json.dumps(dict(payload), separators=(",", ":")).encode("utf-8")
    request = Request(
        f"{base_url}{path}",
        data=body,
        method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit operator-provided HTTPS endpoint.
            raw = response.read()
            status = response.status
    except HTTPError as exc:
        raise VerificationError(f"{method} {path} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise VerificationError(f"{method} {path} could not reach the public runtime") from exc
    elapsed = round(time.perf_counter() - started, 3)
    if status < 200 or status >= 300:
        raise VerificationError(f"{method} {path} returned HTTP {status}")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"{method} {path} returned invalid JSON") from exc
    if not isinstance(parsed, Mapping):
        raise VerificationError(f"{method} {path} returned a non-object JSON payload")
    return dict(parsed), elapsed


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def validate_agent_contract(review: Mapping[str, Any], *, require_unresolved: bool) -> dict[str, Any]:
    agents = list_of_records(review.get("agents"))
    names = [str(agent.get("agent_name") or "") for agent in agents]
    require(names == EXPECTED_AGENTS, f"agent order mismatch: {names}")
    require(str(review.get("reasoning_status") or "") == "ready", "Qwen runtime did not return reasoning_status=ready")
    require(bool(str(review.get("orchestrator_verdict") or "").strip()), "Orchestrator verdict is missing")

    decision = record(review.get("orchestrator_decision"))
    accepted = [str(value) for value in decision.get("accepted_claim_ids", [])]
    rejected = [str(value) for value in decision.get("rejected_claim_ids", [])]
    unresolved = [str(value) for value in decision.get("unresolved_claim_ids", [])]
    classified = accepted + rejected + unresolved
    require(len(classified) == len(set(classified)), "Orchestrator classified a claim more than once")

    specialist_claim_ids: list[str] = []
    for agent in agents[:3]:
        for claim in list_of_records(agent.get("claims")):
            claim_id = str(claim.get("claim_id") or "").strip()
            require(bool(claim_id), f"{agent.get('agent_name')} returned a claim without claim_id")
            specialist_claim_ids.append(claim_id)
    require(set(specialist_claim_ids) == set(classified), "Orchestrator did not classify every specialist claim exactly once")
    if require_unresolved:
        require(bool(unresolved), "incomplete-evidence scenario did not preserve an unresolved claim")

    return {
        "agents": names,
        "confidence_band": review.get("confidence_band"),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "unresolved": len(unresolved),
        "reasoning_status": review.get("reasoning_status"),
        "model_configured": bool(str(review.get("raw_model") or "").strip()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("PUBLIC_BASE_URL", ""))
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    base_url = args.base_url.strip().rstrip("/")
    parsed = urlparse(base_url)
    require(parsed.scheme == "https" and bool(parsed.netloc), "PUBLIC_BASE_URL must be an absolute HTTPS URL")

    report: dict[str, Any] = {
        "status": "running",
        "base_url": base_url,
        "checks": {},
    }

    health, elapsed = request_json(base_url, "/api/health", timeout=args.timeout)
    require(health.get("status") == "ok", "backend health is not ok")
    report["checks"]["backend_health"] = {"status": "pass", "elapsed_seconds": elapsed}

    qwen, elapsed = request_json(base_url, "/api/qwen-health", timeout=args.timeout)
    require(qwen.get("status") == "configured", "Qwen runtime is not configured")
    require(qwen.get("api_key_configured") is True and qwen.get("model_configured") is True, "Qwen key or model is not configured")
    report["checks"]["qwen_health"] = {"status": "pass", "elapsed_seconds": elapsed}

    models, elapsed = request_json(base_url, "/api/qwen-models", timeout=args.timeout)
    require(models.get("status") == "ok", "Qwen model entitlement probe failed")
    require(models.get("configured_model_visible") is True, "configured Qwen model is not visible")
    report["checks"]["qwen_models"] = {
        "status": "pass",
        "elapsed_seconds": elapsed,
        "visible_model_count": models.get("visible_model_count"),
    }

    provider, elapsed = request_json(base_url, "/api/provider-health", timeout=args.timeout)
    require(provider.get("status") == "configured", "API-Football runtime is not configured")
    require(provider.get("api_key_configured") is True, "API-Football key is not configured")
    report["checks"]["provider_health"] = {
        "status": "pass",
        "elapsed_seconds": elapsed,
        "daily_budget": provider.get("daily_budget"),
        "requests_used_by_process_today": provider.get("requests_used_by_process_today"),
        "provider_requests_remaining": provider.get("provider_requests_remaining"),
    }

    inventory, elapsed = request_json(base_url, "/api/judge-fixtures?days=7&limit=6", timeout=args.timeout)
    fixtures = list_of_records(inventory.get("fixtures"))
    require(inventory.get("status") == "ready" and bool(fixtures), "judge fixture inventory is empty")
    fixture_id = fixtures[0].get("fixture_id")
    require(isinstance(fixture_id, int) and fixture_id > 0, "judge fixture identity is invalid")
    report["checks"]["fixture_inventory"] = {
        "status": "pass",
        "elapsed_seconds": elapsed,
        "fixture_count": len(fixtures),
        "selected_fixture_id": fixture_id,
    }

    provider_review, elapsed = request_json(
        base_url,
        "/api/review-provider-fixture",
        method="POST",
        payload={"fixture_id": fixture_id},
        timeout=args.timeout,
    )
    provider_runtime = record(provider_review.get("provider_runtime"))
    require(provider_runtime.get("source_classification") == "live_provider", "provider review is not marked live_provider")
    require(provider_runtime.get("provider_facts_created_by_qwen") is False, "provider facts were attributed to Qwen")
    provider_summary = validate_agent_contract(provider_review, require_unresolved=False)
    report["checks"]["provider_backed_agent_society"] = {
        "status": "pass",
        "elapsed_seconds": elapsed,
        **provider_summary,
    }

    incomplete_payload = {
        "match_id": "judge-incomplete-evidence",
        "home_team": "Incomplete Evidence Home",
        "away_team": "Incomplete Evidence Away",
        "competition": "Qwen Agent Society Adversarial Test",
        "provider_snapshot": {"observed_fixture_count": 1},
        "recent_form": {},
        "quant_context": {"evidence_completeness": 0.1},
        "news_context": {},
        "golden_dataset": {},
    }
    incomplete_review, elapsed = request_json(
        base_url,
        "/api/review-live-match",
        method="POST",
        payload=incomplete_payload,
        timeout=args.timeout,
    )
    incomplete_summary = validate_agent_contract(incomplete_review, require_unresolved=True)
    require(incomplete_review.get("confidence_band") in {"Low", "Medium"}, "incomplete evidence produced High confidence")
    agents = list_of_records(incomplete_review.get("agents"))
    missing_data = [item for agent in agents for item in agent.get("missing_data", []) if str(item).strip()]
    require(bool(missing_data), "incomplete-evidence scenario did not expose missing data")
    report["checks"]["incomplete_evidence_agent_society"] = {
        "status": "pass",
        "elapsed_seconds": elapsed,
        "missing_data_count": len(missing_data),
        **incomplete_summary,
    }

    report["status"] = "pass"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
