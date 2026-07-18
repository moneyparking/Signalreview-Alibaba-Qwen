# SignalReview AI — Secure Qwen Agent Society

Public hackathon runtime for the **Global AI Hackathon Series with Qwen Cloud**.

This repository contains the isolated, public-safe backend for the SignalReview judge workflow. `deploy.sh` deploys it to Alibaba Cloud ECS, where it can hydrate a bounded evidence packet from API-Football, compute deterministic match context before model inference, and execute four sequential Qwen passes:

`Statistician → Skeptic → Upside Scout → Orchestrator`

The repository intentionally excludes Supabase schemas, authentication, billing, private commercial datasets, production calibration assets, and secrets. Repository readiness is not treated as live deployment proof: the judge environment must also pass the documented ECS, Qwen, provider, and public-UI health checks.

## Hackathon verification matrix

| Requirement | Repository evidence |
| --- | --- |
| Open-source license | Root `LICENSE` contains the MIT License. |
| Alibaba Cloud deployment | `deploy.sh` installs the FastAPI backend as a `systemd` service on Ubuntu 22.04 ECS. |
| Qwen Cloud usage | `live_match_processor.py` calls the configured Model Studio OpenAI-compatible `/chat/completions` endpoint. |
| Agent Society | Four sequential, role-specific Qwen passes with contract validation and deterministic recovery. |
| Live sports evidence | `api_football_provider.py` provides a quota-safe server-side API-Football adapter. |
| Architecture and judge evidence | `docs/submission/qwen-judge-pack/` and the repository source. |

## Runtime architecture

```text
SignalReview judge UI
  → Alibaba Cloud ECS / FastAPI
    → API-Football adapter
       - server-only key
       - current fixture inventory
       - recent form and H2H observations
       - process cache
       - daily request budget
    → deterministic quant adapter
       - lambda estimates
       - 1/X/2 distribution
       - O2.5 and BTTS estimates
       - evidence-completeness discount
    → forensic evidence broker
       - observed provider rows
       - deterministic-derived rows
       - explicit missing domains
    → Statistician Qwen pass
    → Skeptic Qwen pass
    → Upside Scout Qwen pass
    → Orchestrator Qwen pass
    → validated dashboard-ready JSON
```

## Data and safety boundaries

- API-Football facts are fetched only by the ECS backend; the API key is never sent to the browser.
- The adapter reserves quota through `API_FOOTBALL_DAILY_BUDGET` and caches equivalent requests.
- One uncached provider review uses four bounded calls: fixture identity, recent home form, recent away form, and H2H.
- Missing lineups, market references, injuries, news, or provider fields remain explicitly unavailable.
- Lambda, 1/X/2, O2.5, BTTS, and confidence are deterministic model estimates, not provider facts.
- Qwen interprets the evidence packet and resolves disagreement. It cannot create provider facts or deterministic metrics.
- Golden Dataset fields, when supplied, are non-live calibration only.
- No certainty, guaranteed outcome, ROI, accuracy, bookmaker, staking, or gambling instructions are produced.
- Invalid Qwen output triggers deterministic contract-safe recovery.

## Agent contract

### Statistician

Publishes evidence-bound claims and may use only values present in structured refs.

### Skeptic

Challenges the Statistician through the same evidence rows and preserves unresolved gaps.

### Upside Scout

Separates a primary scenario, alternate scenario, observable triggers, and invalidation conditions.

### Orchestrator

Classifies specialist claims as accepted, rejected, or unresolved, applies the evidence ceiling, and publishes the final risk and confidence band.

## Files

```text
.
├── api_football_provider.py       # live provider adapter, quota budget, cache, deterministic quant
├── forensic_data_broker.py        # evidence normalization and provenance
├── live_match_processor.py        # four Qwen agents and validators
├── live_routes.py                 # FastAPI routes
├── main.py                        # FastAPI application
├── deploy.sh                      # Alibaba Cloud ECS deployment manifest
├── requirements.txt               # exact-version dependencies
├── tests/                         # provider/runtime contract tests
├── .env.example                   # names and non-secret defaults only
├── LICENSE                        # MIT License
└── docs/submission/qwen-judge-pack/
```

## Environment

Copy the template and set values through the ECS host secret mechanism:

```bash
cp .env.example .env
```

Required Qwen variables:

```text
QWEN_BASE_URL
QWEN_MODEL
QWEN_API_KEY
QWEN_TIMEOUT_MS
QWEN_TOTAL_TIMEOUT_MS
QWEN_MAX_REPAIR_ATTEMPTS
SIGNALREVIEW_REASONING_PROVIDER=qwen
```

Required live provider variable:

```text
API_FOOTBALL_KEY
```

Quota-safe defaults:

```text
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
API_FOOTBALL_DAILY_BUDGET=80
API_FOOTBALL_CACHE_TTL_SECONDS=900
API_FOOTBALL_TIMEOUT_MS=8000
ALLOWED_ORIGINS=https://signalreview.co
```

The runtime budget is intentionally below the API-Football free-plan daily ceiling, leaving reserve capacity for health and manual verification.

## Local run

Python 3.11 or later is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API

### Backend health

```bash
curl http://127.0.0.1:8000/api/health
```

### Redacted Qwen readiness

```bash
curl http://127.0.0.1:8000/api/qwen-health
curl http://127.0.0.1:8000/api/qwen-models
```

### Redacted provider readiness

```bash
curl http://127.0.0.1:8000/api/provider-health
```

The response reports configuration, process request count, cache size, and provider remaining quota when available. It never returns the key.

### Current judge fixtures

```bash
curl 'http://127.0.0.1:8000/api/judge-fixtures?days=3&limit=6'
```

### Provider-backed four-agent review

```bash
curl -X POST http://127.0.0.1:8000/api/review-provider-fixture \
  -H 'Content-Type: application/json' \
  -d '{"fixture_id": 123456}'
```

The endpoint fetches observed provider evidence, computes deterministic estimates, then runs the four Qwen agents.

### Request-supplied four-agent review

The original controlled path remains available for reproducible missing-data and adversarial tests:

```bash
curl -X POST http://127.0.0.1:8000/api/review-live-match \
  -H 'Content-Type: application/json' \
  -d '{
    "match_id": "public-demo",
    "home_team": "Home Team",
    "away_team": "Away Team",
    "provider_snapshot": {"home_shots": 11, "away_shots": 8},
    "quant_context": {"home_control_index": 0.61, "away_control_index": 0.39}
  }'
```

## Alibaba Cloud ECS deployment

Export the required Qwen and API-Football variables, `REPO_URL`, and optionally the quota/cache settings, then run:

```bash
sudo -E bash deploy.sh
```

The script:

1. validates required server-only variables;
2. installs the runtime dependencies;
3. clones or updates the public repository;
4. writes a permission-restricted `.env`;
5. creates and starts a `systemd` service;
6. verifies backend and provider health locally.

No endpoint, model identifier, API key, production hostname, instance identifier, or account identifier is committed.

## Judge verification pack

- [`JUDGE_VERIFICATION_PACK_SOURCE.md`](docs/submission/qwen-judge-pack/JUDGE_VERIFICATION_PACK_SOURCE.md)
- [`JUDGE_CHECKLIST.md`](docs/submission/qwen-judge-pack/JUDGE_CHECKLIST.md)
- [`DEVPOST_COPY_PATCH.md`](docs/submission/qwen-judge-pack/DEVPOST_COPY_PATCH.md)

The final PDF is uploaded separately to Devpost Additional info.

## License

Released under the MIT License.

SignalReview provides structured sports intelligence and transparent reasoning. It does not provide betting predictions, gambling advice, bookmaker recommendations, staking instructions, certainty, guarantees, or financial advice.
