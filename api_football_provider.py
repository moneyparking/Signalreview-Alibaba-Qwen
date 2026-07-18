"""Quota-safe API-Football adapter for the public Alibaba Qwen judge runtime.

The API key remains server-side. Provider observations are cached, quota bounded, and
converted into explicit observed and deterministic-derived fields before Qwen sees them.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlparse

import httpx

DEFAULT_BASE_URL = "https://v3.football.api-sports.io"
DEFAULT_DAILY_BUDGET = 80
DEFAULT_CACHE_TTL_SECONDS = 900
MAX_FREE_PLAN_REQUESTS_PER_DAY = 100


class ApiFootballConfigurationError(RuntimeError):
    pass


class ApiFootballProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ApiFootballSettings:
    api_key: str
    base_url: str
    daily_budget: int
    cache_ttl_seconds: int
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> "ApiFootballSettings":
        api_key = os.getenv("API_FOOTBALL_KEY", "").strip()
        if not api_key:
            raise ApiFootballConfigurationError("API_FOOTBALL_KEY is required")
        base_url = os.getenv("API_FOOTBALL_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ApiFootballConfigurationError("API_FOOTBALL_BASE_URL must be an absolute HTTPS URL")
        daily_budget = _int_env("API_FOOTBALL_DAILY_BUDGET", DEFAULT_DAILY_BUDGET, minimum=1, maximum=MAX_FREE_PLAN_REQUESTS_PER_DAY)
        cache_ttl = _int_env("API_FOOTBALL_CACHE_TTL_SECONDS", DEFAULT_CACHE_TTL_SECONDS, minimum=60, maximum=86_400)
        timeout_ms = _int_env("API_FOOTBALL_TIMEOUT_MS", 8_000, minimum=1_000, maximum=20_000)
        return cls(api_key=api_key, base_url=base_url, daily_budget=daily_budget, cache_ttl_seconds=cache_ttl, timeout_seconds=timeout_ms / 1000)

    def public_diagnostics(self) -> Dict[str, Any]:
        return {
            "configured": True,
            "base_url_configured": True,
            "api_key_configured": True,
            "daily_budget": self.daily_budget,
            "cache_ttl_seconds": self.cache_ttl_seconds,
        }


def _int_env(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ApiFootballConfigurationError(f"{name} must be an integer") from exc
    if value < minimum or value > maximum:
        raise ApiFootballConfigurationError(f"{name} must be between {minimum} and {maximum}")
    return value


def _record(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return default


def _integer(value: Any, default: int = 0) -> int:
    number = _number(value, float(default))
    return int(number)


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _cache_key(path: str, params: Mapping[str, Any]) -> str:
    raw = json.dumps([path, sorted((str(key), str(value)) for key, value in params.items())], separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}
_QUOTA_LOCK = asyncio.Lock()
_QUOTA_DAY = date.today().isoformat()
_LOCAL_REQUEST_COUNT = 0
_PROVIDER_REMAINING: Optional[int] = None


async def _reserve_request(settings: ApiFootballSettings) -> None:
    global _QUOTA_DAY, _LOCAL_REQUEST_COUNT
    async with _QUOTA_LOCK:
        current_day = datetime.now(timezone.utc).date().isoformat()
        if _QUOTA_DAY != current_day:
            _QUOTA_DAY = current_day
            _LOCAL_REQUEST_COUNT = 0
        if _LOCAL_REQUEST_COUNT >= settings.daily_budget:
            raise ApiFootballProviderError("api_football_daily_budget_exhausted")
        if _PROVIDER_REMAINING is not None and _PROVIDER_REMAINING <= 0:
            raise ApiFootballProviderError("api_football_provider_quota_exhausted")
        _LOCAL_REQUEST_COUNT += 1


async def _update_remaining(response: httpx.Response) -> None:
    global _PROVIDER_REMAINING
    raw = response.headers.get("x-ratelimit-requests-remaining")
    if raw is None:
        return
    try:
        remaining = int(raw)
    except ValueError:
        return
    async with _QUOTA_LOCK:
        _PROVIDER_REMAINING = max(0, remaining)


def api_football_diagnostics() -> Dict[str, Any]:
    try:
        settings = ApiFootballSettings.from_env()
    except ApiFootballConfigurationError as exc:
        return {"status": "misconfigured", "error": str(exc)}
    return {
        "status": "configured",
        **settings.public_diagnostics(),
        "requests_used_by_process_today": _LOCAL_REQUEST_COUNT,
        "provider_requests_remaining": _PROVIDER_REMAINING,
        "cache_entries": len(_CACHE),
    }


class ApiFootballClient:
    def __init__(self, settings: Optional[ApiFootballSettings] = None) -> None:
        self.settings = settings or ApiFootballSettings.from_env()

    async def _get(self, path: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        key = _cache_key(path, params)
        cached = _CACHE.get(key)
        if cached and cached[0] > time.monotonic():
            return dict(cached[1])

        await _reserve_request(self.settings)
        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.get(
                f"{self.settings.base_url}/{path.lstrip('/')}",
                params=dict(params),
                headers={"x-apisports-key": self.settings.api_key, "Accept": "application/json"},
            )
        await _update_remaining(response)
        if response.status_code == 429:
            raise ApiFootballProviderError("api_football_rate_limited")
        if not response.is_success:
            raise ApiFootballProviderError(f"api_football_http_{response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiFootballProviderError("api_football_invalid_json") from exc
        if not isinstance(payload, Mapping):
            raise ApiFootballProviderError("api_football_invalid_payload")
        errors = payload.get("errors")
        if errors and errors != [] and errors != {}:
            raise ApiFootballProviderError("api_football_provider_error")
        result = dict(payload)
        _CACHE[key] = (time.monotonic() + self.settings.cache_ttl_seconds, result)
        return result

    async def list_judge_fixtures(self, *, days: int = 3, limit: int = 6) -> Dict[str, Any]:
        bounded_days = max(1, min(days, 7))
        bounded_limit = max(1, min(limit, 12))
        start = datetime.now(timezone.utc).date()
        end = start + timedelta(days=bounded_days - 1)
        payload = await self._get("fixtures", {"from": start.isoformat(), "to": end.isoformat(), "timezone": "UTC"})
        fixtures = [_fixture_summary(item) for item in _list(payload.get("response"))]
        fixtures = [item for item in fixtures if item]
        fixtures.sort(key=lambda item: (0 if item["status_short"] in {"NS", "TBD"} else 1, item["kickoff_utc"], item["fixture_id"]))
        return {
            "status": "ready" if fixtures else "empty",
            "source": "api-football",
            "source_classification": "live_provider",
            "generated_at": _iso_now(),
            "fixtures": fixtures[:bounded_limit],
            "quota": {
                "local_daily_budget": self.settings.daily_budget,
                "requests_used_by_process_today": _LOCAL_REQUEST_COUNT,
                "provider_requests_remaining": _PROVIDER_REMAINING,
            },
        }

    async def build_match_context(self, fixture_id: int) -> Dict[str, Any]:
        fixture_payload = await self._get("fixtures", {"id": fixture_id})
        rows = _list(fixture_payload.get("response"))
        if not rows:
            raise ApiFootballProviderError("api_football_fixture_not_found")
        row = _record(rows[0])
        fixture = _record(row.get("fixture"))
        league = _record(row.get("league"))
        teams = _record(row.get("teams"))
        home = _record(teams.get("home"))
        away = _record(teams.get("away"))
        home_id = _integer(home.get("id"))
        away_id = _integer(away.get("id"))
        if not home_id or not away_id:
            raise ApiFootballProviderError("api_football_fixture_identity_missing")

        home_recent_payload, away_recent_payload, h2h_payload = await asyncio.gather(
            self._get("fixtures", {"team": home_id, "last": 5}),
            self._get("fixtures", {"team": away_id, "last": 5}),
            self._get("fixtures/headtohead", {"h2h": f"{home_id}-{away_id}", "last": 5}),
        )
        home_form = _team_form(_list(home_recent_payload.get("response")), home_id)
        away_form = _team_form(_list(away_recent_payload.get("response")), away_id)
        h2h = _h2h_summary(_list(h2h_payload.get("response")), home_id, away_id)
        quant = _deterministic_quant(home_form, away_form, h2h)
        kickoff = str(fixture.get("date") or "")
        status = _record(fixture.get("status"))
        venue = _record(fixture.get("venue"))
        competition = str(league.get("name") or "Provider fixture")
        home_name = str(home.get("name") or "Home team")
        away_name = str(away.get("name") or "Away team")
        observed_domains = ["fixture", "recent_form", "h2h"]
        missing_domains = ["official_lineups", "external_market_reference", "verified_injuries"]
        return {
            "match_id": f"api-football-{fixture_id}",
            "home_team": home_name,
            "away_team": away_name,
            "competition": competition,
            "kickoff_utc": kickoff or None,
            "venue": str(venue.get("name") or "") or None,
            "provider_snapshot": {
                "fixture_id": fixture_id,
                "league_id": _integer(league.get("id")),
                "season": _integer(league.get("season")),
                "status_elapsed_minutes": _integer(status.get("elapsed")),
                "home_recent_matches": home_form["matches"],
                "away_recent_matches": away_form["matches"],
                "h2h_matches": h2h["matches"],
                "provider_network_calls_for_uncached_review": 4,
            },
            "recent_form": {
                "home": home_form,
                "away": away_form,
                "h2h": h2h,
            },
            "quant_context": quant,
            "news_context": {},
            "golden_dataset": {},
            "provider_provenance": {
                "provider": "api-football",
                "source_classification": "live_provider",
                "fetched_at": _iso_now(),
                "observed_domains": observed_domains,
                "missing_domains": missing_domains,
                "zero_fabrication_policy": True,
                "model_estimates_are_not_provider_facts": True,
            },
        }


def _fixture_summary(value: Any) -> Optional[Dict[str, Any]]:
    row = _record(value)
    fixture = _record(row.get("fixture"))
    league = _record(row.get("league"))
    teams = _record(row.get("teams"))
    home = _record(teams.get("home"))
    away = _record(teams.get("away"))
    fixture_id = _integer(fixture.get("id"))
    if not fixture_id or not home.get("name") or not away.get("name"):
        return None
    status = _record(fixture.get("status"))
    return {
        "fixture_id": fixture_id,
        "match_id": f"api-football-{fixture_id}",
        "home_team": str(home.get("name")),
        "away_team": str(away.get("name")),
        "competition": str(league.get("name") or "Provider fixture"),
        "country": str(league.get("country") or ""),
        "season": _integer(league.get("season")),
        "kickoff_utc": str(fixture.get("date") or ""),
        "status_short": str(status.get("short") or "unknown"),
        "status_long": str(status.get("long") or "unknown"),
        "source": "api-football",
        "source_classification": "live_provider",
    }


def _team_form(rows: list[Any], team_id: int) -> Dict[str, Any]:
    matches = wins = draws = losses = 0
    goals_for = goals_against = 0
    for value in rows[:5]:
        row = _record(value)
        teams = _record(row.get("teams"))
        home = _record(teams.get("home"))
        away = _record(teams.get("away"))
        goals = _record(row.get("goals"))
        home_id = _integer(home.get("id"))
        away_id = _integer(away.get("id"))
        if team_id not in {home_id, away_id}:
            continue
        home_goals = _integer(goals.get("home"))
        away_goals = _integer(goals.get("away"))
        own = home_goals if team_id == home_id else away_goals
        conceded = away_goals if team_id == home_id else home_goals
        matches += 1
        goals_for += own
        goals_against += conceded
        if own > conceded:
            wins += 1
        elif own == conceded:
            draws += 1
        else:
            losses += 1
    divisor = matches or 1
    points = wins * 3 + draws
    return {
        "matches": matches,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "points_per_game": round(points / divisor, 3),
        "goals_for_per_game": round(goals_for / divisor, 3),
        "goals_against_per_game": round(goals_against / divisor, 3),
        "goal_balance_per_game": round((goals_for - goals_against) / divisor, 3),
    }


def _h2h_summary(rows: list[Any], home_id: int, away_id: int) -> Dict[str, Any]:
    matches = home_wins = draws = away_wins = 0
    for value in rows[:5]:
        row = _record(value)
        teams = _record(row.get("teams"))
        fixture_home = _record(teams.get("home"))
        fixture_away = _record(teams.get("away"))
        goals = _record(row.get("goals"))
        fixture_home_id = _integer(fixture_home.get("id"))
        fixture_away_id = _integer(fixture_away.get("id"))
        if {fixture_home_id, fixture_away_id} != {home_id, away_id}:
            continue
        home_goals = _integer(goals.get("home"))
        away_goals = _integer(goals.get("away"))
        matches += 1
        if home_goals == away_goals:
            draws += 1
        else:
            winner_id = fixture_home_id if home_goals > away_goals else fixture_away_id
            if winner_id == home_id:
                home_wins += 1
            elif winner_id == away_id:
                away_wins += 1
    divisor = matches or 1
    return {
        "matches": matches,
        "home_team_win_share": round(home_wins / divisor, 3),
        "draw_share": round(draws / divisor, 3),
        "away_team_win_share": round(away_wins / divisor, 3),
    }


def _deterministic_quant(home: Mapping[str, Any], away: Mapping[str, Any], h2h: Mapping[str, Any]) -> Dict[str, Any]:
    home_attack = _number(home.get("goals_for_per_game"), 1.0)
    home_defence = _number(home.get("goals_against_per_game"), 1.0)
    away_attack = _number(away.get("goals_for_per_game"), 1.0)
    away_defence = _number(away.get("goals_against_per_game"), 1.0)
    lambda_home = round(max(0.2, min(4.0, (home_attack + away_defence) / 2)), 3)
    lambda_away = round(max(0.2, min(4.0, (away_attack + home_defence) / 2)), 3)
    probabilities = _poisson_probabilities(lambda_home, lambda_away)
    observed_matches = _integer(home.get("matches")) + _integer(away.get("matches")) + _integer(h2h.get("matches"))
    completeness = round(min(1.0, observed_matches / 15), 3)
    model_confidence = round(35 + completeness * 40, 1)
    effective_confidence = round(model_confidence * (0.82 if completeness < 0.8 else 0.9), 1)
    return {
        "schema_version": "api_football_deterministic_quant.v1",
        "calculation_owner": "signalreview_deterministic_adapter",
        "provider_facts_created_by_model": False,
        "lambda_home": lambda_home,
        "lambda_away": lambda_away,
        "home_win": probabilities["home_win"],
        "draw": probabilities["draw"],
        "away_win": probabilities["away_win"],
        "over_2_5": probabilities["over_2_5"],
        "btts": probabilities["btts"],
        "model_confidence": model_confidence,
        "effective_confidence": effective_confidence,
        "evidence_completeness": completeness,
        "observed_match_count": observed_matches,
        "responsible_use": "model estimates; not provider facts, certainty, odds, or outcome guarantees",
    }


def _poisson_probabilities(lambda_home: float, lambda_away: float, max_goals: int = 8) -> Dict[str, float]:
    home_win = draw = away_win = over_2_5 = btts = total_mass = 0.0
    for home_goals in range(max_goals + 1):
        home_p = math.exp(-lambda_home) * (lambda_home ** home_goals) / math.factorial(home_goals)
        for away_goals in range(max_goals + 1):
            away_p = math.exp(-lambda_away) * (lambda_away ** away_goals) / math.factorial(away_goals)
            probability = home_p * away_p
            total_mass += probability
            if home_goals > away_goals:
                home_win += probability
            elif home_goals == away_goals:
                draw += probability
            else:
                away_win += probability
            if home_goals + away_goals > 2:
                over_2_5 += probability
            if home_goals > 0 and away_goals > 0:
                btts += probability
    divisor = total_mass or 1.0
    return {
        "home_win": round(home_win / divisor, 4),
        "draw": round(draw / divisor, 4),
        "away_win": round(away_win / divisor, 4),
        "over_2_5": round(over_2_5 / divisor, 4),
        "btts": round(btts / divisor, 4),
    }


__all__ = [
    "ApiFootballClient",
    "ApiFootballConfigurationError",
    "ApiFootballProviderError",
    "ApiFootballSettings",
    "api_football_diagnostics",
]
