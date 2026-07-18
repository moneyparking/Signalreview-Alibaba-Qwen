# SignalReview AI — Secure Qwen Agent Society

Public hackathon runtime for the Global AI Hackathon Series with Qwen Cloud.

This repository contains an isolated, public-safe implementation of the SignalReview four-agent debate core. It intentionally excludes the private commercial platform, including Supabase schemas and migrations, authentication/account code, billing/subscription integrations, private datasets, production calibration assets, and secrets.

## Hackathon verification matrix

| Judging requirement | Repository evidence |
| --- | --- |
| Open-source license | Root-level `LICENSE` contains the complete MIT License text. |
| Alibaba Cloud deployment | `deploy.sh` is an explicit Alibaba Cloud ECS deployment manifest for Ubuntu 22.04 LTS and installs the API as a `systemd` service. |
| Qwen model usage | `live_match_processor.py` calls the configured Alibaba Cloud Model Studio OpenAI-compatible `/chat/completions` API with `QWEN_MODEL` and `QWEN_API_KEY`. |
| Reproducibility | `requirements.txt` uses exact `==` pins; local and ECS run instructions are documented below. |
| Agent Society track | Statistician, Skeptic, Upside Scout, and Orchestrator execute as four sequential, contract-validated Qwen passes. |
| Judge verification source | `docs/submission/qwen-judge-pack/` maps current source, data states, deployment evidence, judge checks, and Devpost corrections. |

## Judge verification pack

- [`JUDGE_VERIFICATION_PACK_SOURCE.md`](docs/submission/qwen-judge-pack/JUDGE_VERIFICATION_PACK_SOURCE.md) — source text and evidence mapping.
- [`JUDGE_CHECKLIST.md`](docs/submission/qwen-judge-pack/JUDGE_CHECKLIST.md) — final operator checklist.
- [`DEVPOST_COPY_PATCH.md`](docs/submission/qwen-judge-pack/DEVPOST_COPY_PATCH.md) — exact replacement copy for current submission mismatches.

The final PDF is generated as a submission artifact and uploaded manually to Devpost Additional info. It is intentionally not required for runtime installation.

## Verified Alibaba Cloud deployment evidence

The project was deployed and operationally verified on Alibaba Cloud infrastructure before the paid resources were intentionally stopped to prevent further cloud charges. The verified environment included:

- Alibaba Cloud Elastic Compute Service in the Germany (Frankfurt) region;
- Ubuntu 22.04 LTS on an ECS instance;
- public and private network interfaces with an attached security group;
- Alibaba Cloud Model Studio with an OpenAI-compatible API host supplied at runtime;
- a server-side, environment-selected Qwen model deployment.

The stopped ECS state does not change reproducibility: `deploy.sh` recreates the documented service on a compatible Ubuntu 22.04 ECS host. Workspace identifiers, instance identifiers, IP addresses, API hosts, model identifiers, and credentials are deliberately not hardcoded in this public repository. The workspace-specific OpenAI-compatible API base URL and selected model are supplied at runtime through `QWEN_BASE_URL` and `QWEN_MODEL`.

## Runtime architecture

```text
request payload
  -> forensic_data_broker.py
     -> request-supplied provider adapter
     -> deterministic quant-context adapter
     -> non-live Golden Dataset adapter
     -> qualitative news-context adapter
     -> content-addressed process cache
  -> Statistician Qwen pass
  -> Skeptic Qwen pass
  -> Upside Scout Qwen pass
  -> Orchestrator Qwen pass
  -> validated dashboard-ready JSON
```

The broker performs **zero external provider calls** in the request path. Repeated equivalent payloads reuse a content-addressed in-process cache, preventing duplicate provider fan-out and preserving quota discipline.

**API-Football is disabled and is not an active source in this isolated public runtime.** Provider observations are supplied in the request. The model cannot invent or fetch missing provider facts.

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
├── deploy.sh                 # Alibaba Cloud ECS deployment manifest
├── requirements.txt          # exact-version runtime dependencies
├── .env.example              # empty Vercel/Qwen variable names only
├── LICENSE                   # MIT License
├── docs/submission/qwen-judge-pack/
└── README.md
```

## Qwen / Alibaba Cloud Model Studio integration

The runtime uses the official OpenAI-compatible Qwen API contract exposed by Alibaba Cloud Model Studio. `QWEN_BASE_URL` must contain the official workspace-specific or region-specific Model Studio base URL available to the deployment account; the application appends `/chat/completions` at runtime.

`SIGNALREVIEW_REASONING_PROVIDER` must be set to `qwen`. The model remains environment-configurable through `QWEN_MODEL` so judges can use the Qwen deployment enabled for their region, workspace, or hackathon entitlement without modifying source code.

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

## Local run

Python 3.11 or later is recommended. Runtime dependencies are exact-version pinned in `requirements.txt` for reproducible automated builds.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
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

## Alibaba Cloud ECS deployment

`deploy.sh` targets Ubuntu 22.04 LTS on Alibaba Cloud Elastic Compute Service. Export all seven required runtime variables and `REPO_URL` through the host secret mechanism, then run:

```bash
sudo -E bash deploy.sh
```

The deployment script:

1. validates every required Qwen runtime variable;
2. installs Git, Python, venv, pip, and curl;
3. clones or updates the public repository;
4. installs exact-version Python dependencies;
5. writes a permission-restricted runtime `.env`;
6. creates and starts a `systemd` service;
7. verifies `/api/health` locally.

The script refuses to create the service when any required runtime variable is absent. It contains no embedded Qwen endpoint, model, timeout, repair-limit, API key, or production hostname.

## Security boundary

The public repository must never contain:

- Supabase migrations, schemas, URLs, anon keys, or service-role keys;
- authentication, profile, watchlist persistence, or account screens;
- WayForPay, crypto billing, subscription, entitlement, or webhook code;
- private API keys, database URLs, access tokens, or production hostnames;
- proprietary commercial datasets, sealed packs, private calibration tables, or production artifact pipelines.

## License

Released under the MIT License. See the root-level `LICENSE` file.

SignalReview provides structured sports intelligence and transparent reasoning. It does not provide betting predictions, gambling advice, bookmaker recommendations, staking instructions, certainty, guarantees, or financial advice.
