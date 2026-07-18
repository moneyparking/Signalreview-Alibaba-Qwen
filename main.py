from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from live_routes import router as live_router

load_dotenv()


def allowed_origins() -> List[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="SignalReview Alibaba Qwen Hackathon API",
    description="Isolated open-source Qwen Cloud Agent Society with a quota-safe API-Football evidence adapter.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(live_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "SignalReview Alibaba Qwen Hackathon API",
        "status": "ok",
        "docs": "/docs",
        "health": "/api/health",
        "provider_health": "/api/provider-health",
        "judge_fixtures": "/api/judge-fixtures",
        "review_endpoint": "/api/review-live-match",
        "provider_review_endpoint": "/api/review-provider-fixture",
    }
