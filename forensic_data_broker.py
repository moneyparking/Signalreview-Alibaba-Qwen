"""Public-safe forensic evidence broker for the SignalReview Qwen hackathon runtime.

The broker never performs provider network calls. It only adapts data already supplied
with the request, deduplicates repeated payloads in-process, and emits a compact,
auditable evidence packet for the four-agent debate.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

BROKER_SCHEMA_VERSION = "signalreview.public_forensic_broker.v1"
CACHE_MAX_ENTRIES = 128

_EVIDENCE_PRIORITY = {
    "provider_observed": 500,
    "deterministic_derived": 400,
    "golden_non_live": 300,
    "context_observed": 200,
    "unavailable": 0,
}

_ID_LIKE_KEY = re.compile(r"(?:^|_)(?:id|uuid|key|token|secret|fixture_id|team_id|player_id)(?:$|_)", re.IGNORECASE)
_NUMERIC_KEY = re.compile(r"[^a-z0-9]+")


def _record(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _finite_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        cleaned = value.strip().replace("%", "")
        if not cleaned:
            return None
        try:
            number = float(cleaned)
        except ValueError:
            return None
    else:
        return None
    return number if math.isfinite(number) else None


def _slug(value: str) -> str:
    cleaned = _NUMERIC_KEY.sub("_", value.lower()).strip("_")
    return cleaned[:72] or "metric"


def _label(value: str) -> str:
    return " ".join(part for part in re.split(r"[_./-]+", value) if part).strip().title() or "Metric"


def _unit_for(path: str, raw_value: Any) -> Optional[str]:
    lowered = path.lower()
    if isinstance(raw_value, str) and raw_value.strip().endswith("%"):
        return "%"
    if any(token in lowered for token in ("percent", "percentage", "_pct", "probability")):
        return "%"
    if any(token in lowered for token in ("minute", "minutes", "_min")):
        return "min"
    if lowered.endswith("_ms"):
        return "ms"
    return None


def _iter_numeric_leaves(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any, float]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if _ID_LIKE_KEY.search(key_text):
                continue
            yield from _iter_numeric_leaves(item, (*path, key_text))
        return
    if isinstance(value, list):
        for index, item in enumerate(value[:20]):
            yield from _iter_numeric_leaves(item, (*path, str(index)))
        return
    number = _finite_number(value)
    if number is not None and path:
        yield path, value, number


def _rows_from_payload(
    payload: Mapping[str, Any],
    *,
    namespace: str,
    source: str,
    evidence_tier: str,
    claim_tag: str,
    live: bool,
) -> list[Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []
    for path, raw_value, number in _iter_numeric_leaves(payload):
        path_text = ".".join(path)
        ref = f"{namespace}_{_slug(path_text)}"
        rows.append(
            {
                "ref": ref,
                "label": _label(path_text),
                "value": number,
                "unit": _unit_for(path_text, raw_value),
                "source": source,
                "evidence_tier": evidence_tier,
                "claim_tag": claim_tag,
                "live": live,
                "public_text_policy": "label_and_exact_value_only;raw_ref_hidden",
            }
        )
    return rows


class _EvidenceCache:
    def __init__(self, max_entries: int = CACHE_MAX_ENTRIES) -> None:
        self._max_entries = max_entries
        self._items: MutableMapping[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            payload = self._items.get(key)
            if payload is None:
                return None
            self._items.move_to_end(key)
            return deepcopy(payload)

    def put(self, key: str, payload: Mapping[str, Any]) -> None:
        with self._lock:
            self._items[key] = deepcopy(dict(payload))
            self._items.move_to_end(key)
            while len(self._items) > self._max_entries:
                self._items.popitem(last=False)


_CACHE = _EvidenceCache()


class ProviderSnapshotAdapter:
    adapter_id = "provider_snapshot_request_adapter"

    def adapt(self, context: Mapping[str, Any]) -> Dict[str, Any]:
        provider_snapshot = _record(context.get("provider_snapshot"))
        recent_form = _record(context.get("recent_form"))
        rows = _rows_from_payload(
            provider_snapshot,
            namespace="provider",
            source="request.provider_snapshot",
            evidence_tier="provider_observed",
            claim_tag="data_backed",
            live=True,
        )
        rows.extend(
            _rows_from_payload(
                recent_form,
                namespace="form",
                source="request.recent_form",
                evidence_tier="context_observed",
                claim_tag="data_backed",
                live=True,
            )
        )
        return {
            "adapter_id": self.adapter_id,
            "rows": rows,
            "status": "bound" if provider_snapshot or recent_form else "unavailable",
            "quota_policy": "reuse_request_payload;zero_provider_network_calls",
        }


class QuantContextAdapter:
    adapter_id = "quant_context_request_adapter"

    def adapt(self, context: Mapping[str, Any]) -> Dict[str, Any]:
        quant_context = _record(context.get("quant_context"))
        rows = _rows_from_payload(
            quant_context,
            namespace="quant",
            source="request.quant_context",
            evidence_tier="deterministic_derived",
            claim_tag="data_backed",
            live=True,
        )
        return {
            "adapter_id": self.adapter_id,
            "rows": rows,
            "status": "bound" if rows else "unavailable",
            "calculation_owner": "upstream deterministic math layer",
        }


class GoldenDatasetAdapter:
    adapter_id = "golden_dataset_request_adapter"

    def adapt(self, context: Mapping[str, Any]) -> Dict[str, Any]:
        golden_dataset = _record(context.get("golden_dataset"))
        rows = _rows_from_payload(
            golden_dataset,
            namespace="golden",
            source="request.golden_dataset",
            evidence_tier="golden_non_live",
            claim_tag="data_backed",
            live=False,
        )
        return {
            "adapter_id": self.adapter_id,
            "rows": rows,
            "status": "bound_non_live" if rows else "unavailable",
            "policy": "calibration_only;never_live_fixture_truth;never_outcome_accuracy",
        }


class NewsContextAdapter:
    adapter_id = "news_context_request_adapter"

    def adapt(self, context: Mapping[str, Any]) -> Dict[str, Any]:
        news_context = _record(context.get("news_context"))
        return {
            "adapter_id": self.adapter_id,
            "status": "bound" if news_context else "unavailable",
            "safe_keys": sorted(str(key) for key in news_context.keys() if not _ID_LIKE_KEY.search(str(key)))[:20],
            "rows": [],
            "policy": "qualitative_context_only;no_injury_or_private_news_invention",
        }


class ForensicDataBroker:
    """Build a deterministic, quota-safe evidence packet from request-supplied data."""

    def __init__(self) -> None:
        self._adapters = (
            ProviderSnapshotAdapter(),
            QuantContextAdapter(),
            GoldenDatasetAdapter(),
            NewsContextAdapter(),
        )

    def build(self, context: Mapping[str, Any]) -> Dict[str, Any]:
        safe_context = {
            "match_id": str(context.get("match_id") or ""),
            "home_team": str(context.get("home_team") or ""),
            "away_team": str(context.get("away_team") or ""),
            "competition": context.get("competition"),
            "kickoff_utc": context.get("kickoff_utc"),
            "venue": context.get("venue"),
            "provider_snapshot": _record(context.get("provider_snapshot")),
            "recent_form": _record(context.get("recent_form")),
            "quant_context": _record(context.get("quant_context")),
            "news_context": _record(context.get("news_context")),
            "golden_dataset": _record(context.get("golden_dataset")),
        }
        cache_key = _fingerprint(safe_context)
        cached = _CACHE.get(cache_key)
        if cached is not None:
            cached["diagnostics"]["cache_status"] = "hit"
            return cached

        adapter_outputs = [adapter.adapt(safe_context) for adapter in self._adapters]
        selected: Dict[str, Dict[str, Any]] = {}
        for output in adapter_outputs:
            for row in output.get("rows", []):
                ref = str(row.get("ref") or "")
                tier = str(row.get("evidence_tier") or "unavailable")
                if not ref or tier not in _EVIDENCE_PRIORITY:
                    continue
                current = selected.get(ref)
                if current is None or _EVIDENCE_PRIORITY[tier] > _EVIDENCE_PRIORITY[str(current["evidence_tier"])]:
                    selected[ref] = dict(row)

        rows = sorted(selected.values(), key=lambda row: (-_EVIDENCE_PRIORITY[str(row["evidence_tier"])], str(row["ref"])))
        domains = {
            "provider_snapshot": bool(safe_context["provider_snapshot"]),
            "recent_form": bool(safe_context["recent_form"]),
            "quant_context": bool(safe_context["quant_context"]),
            "news_context": bool(safe_context["news_context"]),
            "golden_dataset": bool(safe_context["golden_dataset"]),
        }
        packet = {
            "schema_version": BROKER_SCHEMA_VERSION,
            "match": {
                "home_team": safe_context["home_team"],
                "away_team": safe_context["away_team"],
                "competition": safe_context["competition"],
                "kickoff_utc": safe_context["kickoff_utc"],
                "venue": safe_context["venue"],
            },
            "rows": rows,
            "canonical_refs": [row["ref"] for row in rows],
            "missing_domains": [name for name, present in domains.items() if not present],
            "golden_dataset_status": next(
                (output["status"] for output in adapter_outputs if output["adapter_id"] == GoldenDatasetAdapter.adapter_id),
                "unavailable",
            ),
            "diagnostics": {
                "cache_status": "miss",
                "cache_fingerprint": cache_key[:16],
                "adapter_statuses": [
                    {"adapter_id": output["adapter_id"], "status": output["status"]} for output in adapter_outputs
                ],
                "published_row_count": len(rows),
                "quota_policy": "request_payload_reuse_and_content_addressed_process_cache",
                "network_calls": 0,
            },
            "public_contract": {
                "raw_refs_allowed_only_in_structured_refs": True,
                "raw_refs_forbidden_in_debate_text": True,
                "golden_dataset_is_non_live": True,
                "missing_domains_can_only_reduce_confidence": True,
            },
        }
        _CACHE.put(cache_key, packet)
        return deepcopy(packet)


__all__ = [
    "BROKER_SCHEMA_VERSION",
    "ForensicDataBroker",
    "GoldenDatasetAdapter",
    "ProviderSnapshotAdapter",
    "QuantContextAdapter",
]
