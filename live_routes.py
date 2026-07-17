"""FastAPI routes for the isolated SignalReview Alibaba Qwen hackathon runtime."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from live_match_processor import (
    MatchContext,
    RuntimeConfigurationError,
    build_processor_from_env,
    qwen_models_probe,
    qwen_runtime_diagnostics,
)

router = APIRouter(prefix="/api", tags=["qwen-live-review"])


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
