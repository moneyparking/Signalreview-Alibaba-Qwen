# SignalReview AI — Secure Qwen Agent Society

Public hackathon repository for the **Global AI Hackathon Series with Qwen Cloud**, Track 3: Agent Society.

SignalReview turns a bounded football evidence packet into a four-role adversarial review:

`Statistician → Skeptic → Upside Scout → Orchestrator`

The system is decision-support software. It is not a bookmaker, sportsbook, capper, guaranteed-picks, staking, or certainty product.

## Judge path

- Public UI: `https://signalreview.co/dashboard`
- Public video: `https://youtu.be/3GKHrsXoqII`
- Public repository: this repository
- License: root `LICENSE` (MIT)
- Alibaba deployment manifest: `deploy.sh`

The public Match Board pins a clearly labelled **Qwen Judge Reference Review**. Select that row and click **ENGAGE Qwen Agent Society**.

Expected visible result:

1. a canonical 30-row Quant Passport registry;
2. truthful evidence coverage rather than a hardcoded readiness score;
3. Statistician, Skeptic, Upside Scout, and Orchestrator outputs;
4. Qwen reasoning validation;
5. accepted, rejected, and unresolved findings;
6. a visible evidence-contract state and confidence ceiling;
7. explicit missing market, confirmed-lineup, injury, and provider-observed domains.

The reference is an immutable pre-match evidence snapshot retained for judging. It is labelled as a **reference review**, not as a live match. No post-match result is used in the packet.

Additional upcoming rows may appear from versioned official schedule snapshots or a live provider. Schedule-only rows are discovery identities and do not inherit another fixture's evidence or run Qwen until a fixture-specific packet is bound.

## What is open sourced here

This repository is the isolated, public-safe Qwen runtime and Alibaba Cloud deployment implementation. It excludes private commercial schemas, authentication, billing, user data, proprietary calibration assets, and secrets.

```text
Judge UI
  → server-side evidence packet
    → deterministic evidence normalization
      → Qwen Cloud Statistician
      → Qwen Cloud Skeptic
      → Qwen Cloud Upside Scout
      → Qwen Cloud Orchestrator
        → validated dashboard-ready JSON
```

The included API-Football adapter is an optional quota-safe live-provider path. The judge reference path does not depend on provider availability. Missing provider domains remain unavailable rather than being fabricated.

## Hackathon verification matrix

| Requirement | Evidence |
| --- | --- |
| Qwen Cloud use | `live_match_processor.py` calls the Alibaba Cloud Model Studio OpenAI-compatible chat-completions endpoint. |
| Agent Society | Four role-specific Qwen passes with schema, evidence-reference, disposition, and safety validation. |
| Alibaba Cloud deployment code | `deploy.sh` installs the public-safe FastAPI runtime on Ubuntu ECS behind Caddy HTTPS. |
| Open-source code | Public repository with reproducible runtime files and tests. |
| Open-source license | Root MIT `LICENSE`. |
| Architecture | `docs/submission/qwen-judge-pack/` plus the runtime diagram below. |
| Judge testing access | Public `/dashboard` path; no account or payment required for the reference review. |
| Missing-data safety | Unsupported domains remain visible and confidence-lowering. |
| Reproducibility | Local instructions, exact dependencies, tests, deployment script, and runtime verifier. |

## Runtime architecture

```text
SignalReview public UI
  → server-only analysis route
    → canonical fixture identity
    → evidence broker
       - observed historical evidence
       - deterministic-derived evidence
       - estimated projections
       - blocked/null domains
    → 30-row Quant Passport
    → Qwen Cloud structured reasoning
       - Statistician
       - Skeptic
       - Upside Scout
       - Orchestrator
    → evidence-bound result
       - reasoning status
       - evidence contract
       - coverage
       - confidence ceiling
       - verdict
```

### Optional Alibaba ECS reference deployment

```text
Browser / server caller
  → HTTPS Caddy on Alibaba Cloud ECS
    → FastAPI on 127.0.0.1
      → optional API-Football adapter
      → deterministic evidence broker
      → four Qwen Cloud role passes
      → validated JSON
```

`deploy.sh` keeps Uvicorn on loopback, configures Caddy for public TLS, and keeps Qwen/provider credentials server-side.

## Data and trust boundaries

- Qwen interprets structured evidence; it does not create provider facts or deterministic metrics.
- Fixture identity sources remain visibly classified.
- Historical observations never become live-provider observations.
- Possible lineups and weather forecasts remain estimated projections.
- Missing market data, confirmed lineups, injuries, private news, and live statistics remain null or unavailable.
- Blocked rows remain visible in the 30-row registry.
- Evidence coverage is computed from non-null bound/partial rows; it is not hardcoded.
- Confidence cannot be raised by historical or projected evidence alone.
- No score, odds, line movement, probability, lambda, ROI, accuracy, outcome, or certainty is invented.
- Invalid Qwen output fails closed to deterministic evidence rather than being relabelled as Qwen success.

## Four-agent contract

### Statistician

Synthesizes only evidence-bound drivers and counter-drivers.

### Skeptic

Challenges the same evidence rows, preserves data scarcity, and constrains confidence.

### Upside Scout

Separates primary and alternate scenarios, observable triggers, and invalidation conditions.

### Orchestrator

Classifies every specialist finding as accepted, rejected, or unresolved and publishes the final bounded verdict.

## Repository files

```text
.
├── api_football_provider.py       # optional provider adapter, budget and cache
├── forensic_data_broker.py        # evidence classes and provenance normalization
├── live_match_processor.py        # Qwen roles, contracts and recovery
├── live_routes.py                 # FastAPI routes
├── main.py                        # FastAPI application
├── deploy.sh                      # Alibaba ECS + Caddy deployment manifest
├── scripts/verify_public_runtime.py
├── requirements.txt
├── tests/
├── .env.example
├── LICENSE
└── docs/submission/qwen-judge-pack/
```

## Environment

Copy the template and provide secrets through the server environment:

```bash
cp .env.example .env
```

Qwen variables:

```text
QWEN_BASE_URL
QWEN_MODEL
QWEN_API_KEY
QWEN_TIMEOUT_MS
QWEN_TOTAL_TIMEOUT_MS
QWEN_MAX_REPAIR_ATTEMPTS
SIGNALREVIEW_REASONING_PROVIDER=qwen
```

Optional live-provider variable:

```text
API_FOOTBALL_KEY
```

Public ECS deployment variable:

```text
PUBLIC_HOSTNAME
```

No secret belongs in source control or browser code.

## Local run

Python 3.11 or later:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Run tests:

```bash
pytest -q
```

## Public-safe API

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/qwen-health
curl http://127.0.0.1:8000/api/qwen-models
curl http://127.0.0.1:8000/api/provider-health
curl 'http://127.0.0.1:8000/api/judge-fixtures?days=7&limit=6'
```

Provider-backed review when a provider fixture exists:

```bash
curl -X POST http://127.0.0.1:8000/api/review-provider-fixture \
  -H 'Content-Type: application/json' \
  -d '{"fixture_id": 123456}'
```

Controlled incomplete-evidence review:

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

1. provision or start an Ubuntu ECS instance;
2. point the public hostname to the instance;
3. allow inbound TCP 80 and 443;
4. keep port 8000 closed publicly;
5. provide Qwen, optional provider, repository, and hostname variables.

Run:

```bash
sudo -E bash deploy.sh
```

The script validates variables, installs dependencies and Caddy, deploys the service, writes a restricted environment file, binds FastAPI to loopback, and checks public HTTPS health.

Repository code proves the Alibaba deployment implementation. A running-instance claim must be supported separately by current console/runtime evidence; this README does not convert deployment code into a false uptime claim.

## Runtime verification

For a deployed public runtime:

```bash
PUBLIC_BASE_URL="https://${PUBLIC_HOSTNAME}" \
  python3 scripts/verify_public_runtime.py
```

The verifier checks health, Qwen readiness, provider readiness when configured, four ordered roles, complete specialist disposition, and a fail-closed incomplete-evidence case. It does not print secrets or raw provider bodies.

## Judge verification pack

- `docs/submission/qwen-judge-pack/JUDGE_VERIFICATION_PACK_SOURCE.md`
- `docs/submission/qwen-judge-pack/JUDGE_CHECKLIST.md`
- `docs/submission/qwen-judge-pack/DEVPOST_COPY_PATCH.md`

The final PDF is uploaded separately to Devpost Additional info.

## License

MIT License. See `LICENSE`.
