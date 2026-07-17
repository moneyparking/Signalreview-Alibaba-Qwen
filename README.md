# SignalReview AI — Secure Qwen Agent Society

Public hackathon runtime for the Global AI Hackathon Series with Qwen Cloud.

This repository contains an isolated, public-safe implementation of the SignalReview four-agent debate core. It intentionally excludes the private commercial platform, including Supabase schemas and migrations, authentication/account code, billing/subscription integrations, private datasets, production calibration assets, and secrets.

## Runtime architecture

```text
request payload
  -> forensic_data_broker.py
     -> request-supplied provider adapter
     -> deterministic quant-context adapter
     -> non-live Golden Dataset adapter
     -> content-addressed process cache
  -> Statistician Qwen pass
  -> Skeptic Qwen pass
  -> Upside Scout Qwen pass
  -> Orchestrator Qwen pass
  -> validated dashboard-ready JSON
```

The broker performs **zero external provider calls** in the request path. Repeated equivalent payloads reuse a content-addressed in-process cache, preventing duplicate provider fan-out and preserving quota discipline.

## Agent contract

### Statistician

Publishes three evidence-bound claims. Every number must exactly match a structured evidence row attached through `refs`.

### Skeptic

Publishes three paired challenges:

- `K1` challenges `S1` through the same evidence ref;
- `K2` challenges `S2` through the same evidence ref;
- `K3` challenges `S3` through the same evidence ref.

### Upside Scout

Separates the primary scenario, alternate scenario, and observable invalidation without converting inference into certainty.

### Orchestrator

Classifies every specialist claim exactly once as accepted, rejected, or unresolved, preserves missing-data constraints, and produces the final confidence band and risk flags.

## Trust and publication rules

- Raw evidence refs are permitted only inside structured `refs` arrays.
- Raw refs and claim IDs are forbidden in customer-facing debate text.
- Golden Dataset fields are non-live calibration context only.
- Missing evidence can only constrain confidence.
- The model cannot invent odds, injuries, line movement, private news, ROI, accuracy, lambdas, or outcomes.
- Gambling, certainty, bookmaker, staking, and guaranteed-outcome language is rejected.
- Invalid Qwen output triggers deterministic contract-safe recovery.

## Files

```text
.
├── forensic_data_broker.py   # quota-safe request adapters and evidence cache
├── live_match_processor.py   # four sequential Qwen agents and validators
├── live_routes.py            # FastAPI routes
├── main.py                   # FastAPI application
├── deploy.sh                 # environment-driven ECS deployment
├── requirements.txt
├── .env.example              # empty Vercel/Qwen variable names only
└── README.md
```

## Environment

Copy the template and provide values through the deployment secret store. The repository does not contain model, endpoint, timeout, repair-limit, or key defaults.

```bash
cp .env.example .env
```

Required variables:

```text
QWEN_BASE_URL
QWEN_MODEL
QWEN_API_KEY
QWEN_TIMEOUT_MS
QWEN_TOTAL_TIMEOUT_MS
QWEN_MAX_REPAIR_ATTEMPTS
SIGNALREVIEW_REASONING_PROVIDER
```

`SIGNALREVIEW_REASONING_PROVIDER` must be set to `qwen` for the live four-agent path.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API

### Health

```bash
curl http://127.0.0.1:8000/api/health
```

### Redacted Qwen configuration health

```bash
curl http://127.0.0.1:8000/api/qwen-health
```

The response reports only whether required fields are configured. It does not expose an API key prefix, endpoint, model name, or provider response body.

### Model entitlement probe

```bash
curl http://127.0.0.1:8000/api/qwen-models
```

The response reports only status, HTTP status, model visibility, and visible model count.

### Four-agent review

```bash
curl -X POST http://127.0.0.1:8000/api/review-live-match \
  -H 'Content-Type: application/json' \
  -d '{
    "match_id": "public-demo",
    "home_team": "Home Team",
    "away_team": "Away Team",
    "provider_snapshot": {
      "home_shots": 11,
      "away_shots": 8
    },
    "quant_context": {
      "home_control_index": 0.61,
      "away_control_index": 0.39
    },
    "golden_dataset": {
      "evidence_convergence": 0.74
    }
  }'
```

## Deployment

Export all seven required runtime variables and `REPO_URL` through the host secret mechanism, then run:

```bash
sudo -E bash deploy.sh
```

The deployment script refuses to create the service when any required runtime variable is absent. It writes the runtime `.env` with restrictive permissions and does not include embedded Qwen endpoint, model, timeout, repair-limit, or secret defaults.

## Security boundary

The public repository must never contain:

- Supabase migrations, schemas, URLs, anon keys, or service-role keys;
- authentication, profile, watchlist persistence, or account screens;
- WayForPay, crypto billing, subscription, entitlement, or webhook code;
- private API keys, database URLs, access tokens, or production hostnames;
- proprietary commercial datasets, sealed packs, private calibration tables, or production artifact pipelines.

SignalReview provides structured sports intelligence and transparent reasoning. It does not provide betting predictions, gambling advice, bookmaker recommendations, staking instructions, certainty, guarantees, or financial advice.
