# SignalReview AI — Secure Qwen Agent Society

Public hackathon runtime for the **Global AI Hackathon Series with Qwen Cloud**.

This repository contains the isolated, public-safe backend for the SignalReview judge workflow. `deploy.sh` deploys it to Alibaba Cloud ECS, hydrates a bounded evidence packet from API-Football, computes deterministic match context before model inference, and executes four sequential Qwen passes:

`Statistician → Skeptic → Upside Scout → Orchestrator`

The repository intentionally excludes Supabase schemas, authentication, billing, private commercial datasets, production calibration assets, and secrets. Repository readiness is not treated as live deployment proof: the judge environment must also pass the documented ECS, TLS, Qwen, provider, Agent Society, and public-UI checks.

## Hackathon verification matrix

| Requirement | Repository evidence |
| --- | --- |
| Open-source license | Root `LICENSE` contains the MIT License. |
| Alibaba Cloud deployment | `deploy.sh` installs FastAPI plus an HTTPS Caddy reverse proxy on Ubuntu 22.04 ECS. |
| Qwen Cloud usage | `live_match_processor.py` calls the configured Model Studio OpenAI-compatible `/chat/completions` endpoint. |
| Agent Society | Four sequential, role-specific Qwen passes with contract validation and deterministic recovery. |
| Live sports evidence | `api_football_provider.py` provides a quota-safe server-side API-Football adapter. |
| Judge verification | `scripts/verify_public_runtime.py` executes health, provider-backed, and incomplete-evidence checks against the public HTTPS runtime. |
| Architecture and submission evidence | `docs/submission/qwen-judge-pack/` and the repository source. |

## Runtime architecture

```text
SignalReview judge UI on Vercel
  → HTTPS public hostname
    → Caddy on Alibaba Cloud ECS
      → FastAPI on 127.0.0.1
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
- Uvicorn binds only to `127.0.0.1`; Caddy owns public ports 80 and 443 and automatically provisions TLS after DNS resolves.

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
├── deploy.sh                      # ECS + systemd + Caddy HTTPS deployment manifest
├── scripts/verify_public_runtime.py
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

Required public deployment variable:

```text
PUBLIC_HOSTNAME
```

`PUBLIC_HOSTNAME` is the hostname only, without `https://`, path, or port. Its DNS A/AAAA record must resolve to the ECS instance before `deploy.sh` performs the final public HTTPS check.

Quota-safe defaults:

```text
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
API_FOOTBALL_DAILY_BUDGET=80
API_FOOTBALL_CACHE_TTL_SECONDS=900
API_FOOTBALL_TIMEOUT_MS=8000
ALLOWED_ORIGINS=https://signalreview.co
```

The runtime budget is below the API-Football free-plan daily ceiling, leaving reserve capacity for health and manual verification.

## Local run

Python 3.11 or later is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
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
curl 'http://127.0.0.1:8000/api/judge-fixtures?days=7&limit=6'
```

### Provider-backed four-agent review

```bash
curl -X POST http://127.0.0.1:8000/api/review-provider-fixture \
  -H 'Content-Type: application/json' \
  -d '{"fixture_id": 123456}'
```

The endpoint fetches observed provider evidence, computes deterministic estimates, then runs the four Qwen agents.

### Request-supplied incomplete-evidence review

```bash
curl -X POST http://127.0.0.1:8000/api/review-live-match \
  -H 'Content-Type: application/json' \
  -d '{
    "match_id": "judge-incomplete-evidence",
    "home_team": "Incomplete Evidence Home",
    "away_team": "Incomplete Evidence Away",
    "provider_snapshot": {"observed_fixture_count": 1},
    "quant_context": {"evidence_completeness": 0.1}
  }'
```

## Alibaba Cloud ECS deployment

Before deployment:

1. start or create an Ubuntu 22.04 ECS instance;
2. point a DNS A/AAAA record for `PUBLIC_HOSTNAME` to the instance;
3. allow inbound TCP 80 and 443 in the ECS security group;
4. keep port 8000 closed publicly;
5. export the Qwen, API-Football, repository, and public-hostname variables.

Run:

```bash
sudo -E bash deploy.sh
```

The script:

1. validates required server-only variables and the public hostname;
2. installs Python runtime dependencies and Caddy;
3. clones or fast-forwards the public repository without discarding unknown local changes;
4. writes a permission-restricted `.env`;
5. creates and starts the loopback-only FastAPI `systemd` service;
6. configures Caddy automatic HTTPS and security headers;
7. verifies local backend/provider health;
8. verifies the public HTTPS health endpoint.

No endpoint, model identifier, API key, production hostname, instance identifier, or account identifier is committed.

## Public end-to-end verification

After DNS, TLS, Qwen, and API-Football are active:

```bash
PUBLIC_BASE_URL="https://${PUBLIC_HOSTNAME}" \
  python3 scripts/verify_public_runtime.py
```

The smoke test fails unless all of the following are true:

- backend, Qwen, model entitlement, and provider health pass;
- at least one current provider fixture is available;
- the provider-backed review returns Statistician, Skeptic, Upside Scout, and Orchestrator in order;
- Qwen reports `reasoning_status=ready`;
- Orchestrator classifies every specialist claim exactly once;
- the incomplete-evidence scenario exposes missing data, avoids High confidence, and retains at least one unresolved claim.

Only the sanitized verification summary is printed; keys and raw provider bodies are never emitted.

## Vercel integration

Set these server-only production variables on the linked SignalReview project:

```text
QWEN_JUDGE_RUNTIME_BASE_URL=https://<PUBLIC_HOSTNAME>
QWEN_JUDGE_RUNTIME_TIMEOUT_MS=48000
```

Redeploy production after changing environment variables. The browser never receives the Qwen or API-Football credentials.

## Judge verification pack

- [`JUDGE_VERIFICATION_PACK_SOURCE.md`](docs/submission/qwen-judge-pack/JUDGE_VERIFICATION_PACK_SOURCE.md)
- [`JUDGE_CHECKLIST.md`](docs/submission/qwen-judge-pack/JUDGE_CHECKLIST.md)
- [`DEVPOST_COPY_PATCH.md`](docs/submission/qwen-judge-pack/DEVPOST_COPY_PATCH.md)

The final PDF is uploaded separately to Devpost Additional info.

## License

Released under the MIT License.

SignalReview provides structured sports intelligence and transparent reasoning. It does not provide betting predictions, gambling advice, bookmaker recommendations, staking instructions, certainty, guarantees, or financial advice.
