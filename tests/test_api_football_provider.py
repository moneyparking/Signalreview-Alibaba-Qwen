from __future__ import annotations

import unittest

from api_football_provider import ApiFootballClient, ApiFootballSettings


class FakeApiFootballClient(ApiFootballClient):
    def __init__(self) -> None:
        super().__init__(
            ApiFootballSettings(
                api_key="test-key",
                base_url="https://example.test",
                daily_budget=80,
                cache_ttl_seconds=900,
                timeout_seconds=5,
            )
        )
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def _get(self, path: str, params):  # type: ignore[override]
        payload = dict(params)
        self.calls.append((path, payload))
        if path == "fixtures" and "from" in payload:
            return {
                "response": [
                    fixture_row(2002, "Later Home", "Later Away", "2026-07-20T18:00:00+00:00"),
                    fixture_row(2001, "Soon Home", "Soon Away", "2026-07-19T18:00:00+00:00"),
                ]
            }
        if path == "fixtures" and payload.get("id") == 2001:
            return {"response": [fixture_row(2001, "Soon Home", "Soon Away", "2026-07-19T18:00:00+00:00")]}
        if path == "fixtures" and payload.get("team") == 11:
            return {"response": recent_rows(11, 22, [(2, 1), (1, 1), (3, 0), (0, 1), (2, 0)])}
        if path == "fixtures" and payload.get("team") == 22:
            return {"response": recent_rows(22, 33, [(1, 0), (0, 0), (1, 2), (2, 1), (1, 1)])}
        if path == "fixtures/headtohead":
            return {"response": recent_rows(11, 22, [(2, 1), (1, 1), (0, 1)])}
        raise AssertionError(f"unexpected provider call: {path} {payload}")


def fixture_row(fixture_id: int, home: str, away: str, kickoff: str):
    return {
        "fixture": {
            "id": fixture_id,
            "date": kickoff,
            "status": {"short": "NS", "long": "Not Started", "elapsed": None},
            "venue": {"name": "Judge Stadium"},
        },
        "league": {"id": 1, "name": "Judge League", "country": "World", "season": 2026},
        "teams": {"home": {"id": 11, "name": home}, "away": {"id": 22, "name": away}},
        "goals": {"home": None, "away": None},
    }


def recent_rows(team_id: int, opponent_id: int, scores: list[tuple[int, int]]):
    rows = []
    for index, (home_goals, away_goals) in enumerate(scores):
        rows.append(
            {
                "fixture": {"id": 3000 + index},
                "teams": {
                    "home": {"id": team_id if index % 2 == 0 else opponent_id, "name": "A"},
                    "away": {"id": opponent_id if index % 2 == 0 else team_id, "name": "B"},
                },
                "goals": {"home": home_goals, "away": away_goals},
            }
        )
    return rows


class ApiFootballAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_lists_real_provider_fixture_summaries(self) -> None:
        client = FakeApiFootballClient()
        result = await client.list_judge_fixtures(days=3, limit=6)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["source_classification"], "live_provider")
        self.assertEqual([row["fixture_id"] for row in result["fixtures"]], [2001, 2002])
        self.assertNotIn("api_key", result)

    async def test_hydrates_observed_evidence_before_qwen(self) -> None:
        client = FakeApiFootballClient()
        context = await client.build_match_context(2001)
        self.assertEqual(context["match_id"], "api-football-2001")
        self.assertEqual(context["home_team"], "Soon Home")
        self.assertEqual(context["away_team"], "Soon Away")
        self.assertEqual(context["provider_provenance"]["source_classification"], "live_provider")
        self.assertTrue(context["provider_provenance"]["zero_fabrication_policy"])
        self.assertEqual(context["provider_snapshot"]["provider_network_calls_for_uncached_review"], 4)
        quant = context["quant_context"]
        self.assertEqual(quant["calculation_owner"], "signalreview_deterministic_adapter")
        self.assertFalse(quant["provider_facts_created_by_model"])
        self.assertGreater(quant["lambda_home"], 0)
        self.assertGreater(quant["lambda_away"], 0)
        self.assertAlmostEqual(quant["home_win"] + quant["draw"] + quant["away_win"], 1.0, places=3)
        self.assertIn("official_lineups", context["provider_provenance"]["missing_domains"])
        self.assertEqual(len(client.calls), 4)


if __name__ == "__main__":
    unittest.main()
