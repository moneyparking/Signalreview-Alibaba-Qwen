"""FastAPI routes for the isolated SignalReview Alibaba Qwen hackathon runtime."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api_football_provider import (
    ApiFootballClient,
    ApiFootballConfigurationError,
    ApiFootballProviderError,
    api_football_diagnostics,
)
from live_match_processor import (
    MatchContext,
    RuntimeConfigurationError,
    build_processor_from_env,
    qwen_models_probe,
    qwen_runtime_diagnostics,
)

router = APIRouter(prefix="/api", tags=["qwen-live-review"])


class ProviderFixtureRequest(BaseModel):
    fixture_id: int = Field(gt=0)


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "signalreview-alibaba-qwen-hackathon",
        "runtime": "fastapi",
    }


@router.get("/qwen-health")
async def qwen_health() -> dict:
    return qwen_runtime_diagnostics()


@router.get("/qwen-models")
async def qwen_models() -> dict:
    return await qwen_models_probe()


@router.get("/provider-health")
async def provider_health() -> dict:
    """Return redacted API-Football readiness and quota diagnostics."""
    return api_football_diagnostics()


@router.get("/judge-fixtures")
async def judge_fixtures(
    days: int = Query(default=3, ge=1, le=7),
    limit: int = Query(default=6, ge=1, le=12),
) -> dict:
    try:
        return await ApiFootballClient().list_judge_fixtures(days=days, limit=limit)
    except ApiFootballConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ApiFootballProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - public boundary suppresses provider internals.
        raise HTTPException(status_code=502, detail="The live fixture adapter could not complete the bounded provider request.") from exc


@router.post("/review-live-match")
async def review_live_match(context: MatchContext) -> dict:
    try:
        processor = build_processor_from_env()
        review = await processor.review_match(context)
        return review.model_dump()
    except RuntimeConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - public boundary deliberately suppresses provider internals.
        raise HTTPException(
            status_code=502,
            detail="The Qwen review runtime could not complete the bounded public contract.",
        ) from exc


@router.post("/review-provider-fixture")
async def review_provider_fixture(request: ProviderFixtureRequest) -> dict:
    """Hydrate one real API-Football fixture, then run the four Qwen agents."""
    try:
        context_payload = await ApiFootballClient().build_match_context(request.fixture_id)
        context = MatchContext(**context_payload)
        processor = build_processor_from_env()
        review = await processor.review_match(context)
        payload = review.model_dump()
        provenance = context_payload.get("provider_provenance", {})
        payload["provider_runtime"] = {
            "provider": "api-football",
            "source_classification": "live_provider",
            "fixture_id": request.fixture_id,
            "provider_facts_created_by_qwen": False,
            "deterministic_quant_created_before_qwen": True,
            "observed_domains": provenance.get("observed_domains", []),
            "missing_domains": provenance.get("missing_domains", []),
        }
        payload["provider_evidence"] = {
            "source": "api-football",
            "source_classification": "live_provider",
            "fixture": {
                "fixture_id": request.fixture_id,
                "home_team": context_payload.get("home_team"),
                "away_team": context_payload.get("away_team"),
                "competition": context_payload.get("competition"),
                "kickoff_utc": context_payload.get("kickoff_utc"),
            },
            "recent_form": context_payload.get("recent_form", {}),
            "availability": {
                "fixture": "available",
                "recent_form": "available",
                "h2h": "available",
                "lineups": "unavailable",
                "market": "unavailable",
                "injuries": "unavailable",
                "news": "unavailable",
            },
        }
        payload["quant_context"] = context_payload.get("quant_context", {})
        return payload
    except ApiFootballConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ApiFootballProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - public boundary deliberately suppresses provider and model internals.
        raise HTTPException(
            status_code=502,
            detail="The provider-backed Qwen Agent Society review could not complete the bounded public contract.",
        ) from exc
