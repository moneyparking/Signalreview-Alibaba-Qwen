# SignalReview AI: Quantum Multi-Agent Sports Intelligence Platform

**SignalReview AI** is a live sports-intelligence agent society built specifically for the **Global AI Hackathon Series with Qwen Cloud**.

The project demonstrates how a production-style multi-agent analysis system can run on Alibaba Cloud infrastructure, route structured reasoning through Qwen Cloud / DashScope OpenAI-compatible APIs, and expose a clean FastAPI contract for live sports review workflows.

This repository is the public, hackathon-safe edition of SignalReview. It is intentionally isolated from the commercial SignalReview.co production stack and contains no private database credentials, no Supabase service-role keys, no billing code, and no proprietary commercial datasets.

---

## Hackathon Track

**Track 3: Agent Society**

SignalReview AI fits the Agent Society track because the core product is not a single chatbot. It is a coordinated society of specialized agents that inspect the same match context from different epistemic positions, debate uncertainty, preserve missing data, and converge into a final orchestrated verdict.

The system is designed for judges to evaluate:

- multi-agent role separation;
- structured reasoning under incomplete evidence;
- safe sports-intelligence output without gambling language;
- Qwen Cloud model integration through an OpenAI-compatible API;
- reproducible backend deployment on Alibaba Cloud ECS.

---

## Product Value

Sports analysis is often reduced to subjective commentary, fragile heuristics, or unsupported certainty. SignalReview AI replaces that pattern with a transparent agent-debate layer.

The product objective is to convert raw match context into a disciplined intelligence brief that clearly distinguishes:

- **data-backed observations**;
- **reasonable inference**;
- **uncertain assumptions**;
- **unavailable evidence**.

Instead of pretending that incomplete data is complete, the platform exposes missing fields directly through the review schema. This is a core product principle: if lineups, market evidence, player events, injury context, or verified provider features are absent, the agents must say so rather than fabricate confidence.

### The Four-Agent Society

#### 1. Statistician

The Statistician evaluates the structured match context mathematically. Its responsibility is to identify what can be inferred from available quantitative signals while refusing to invent unavailable metrics.

Typical focus areas:

- score state and match phase;
- provider evidence quality;
- recent-form signals when supplied;
- quant context when supplied;
- confidence-band discipline.

#### 2. Skeptic

The Skeptic is the adversarial quality-control agent. Its job is to challenge overconfident conclusions, detect missing evidence, and force the final output to remain bounded by verified inputs.

Typical focus areas:

- unavailable lineups;
- unverifiable injuries;
- stale or absent provider data;
- false precision risk;
- uncertainty amplification.

#### 3. Upside Scout

The Upside Scout looks for plausible high-signal scenarios without crossing into certainty. It searches for asymmetric match narratives, tactical context, or momentum hypotheses, but every claim must remain tagged as `data_backed`, `inferred`, `uncertain`, or `unavailable`.

Typical focus areas:

- tactical upside;
- under-discussed context;
- scenario-based analysis;
- qualitative edge discovery;
- upside bounded by evidence quality.

#### 4. Orchestrator

The Orchestrator acts as judge and synthesis layer. It reconciles the other agents, compresses the debate into a structured verdict, and returns the final dashboard-ready JSON.

Typical focus areas:

- final confidence band;
- risk flags;
- transparency notes;
- responsible-use summary;
- schema compliance.

### Model Strategy

The runtime is model-configurable through the `QWEN_MODEL` environment variable.

The target premium reasoning configuration for the agent society is:

```text
qwen2.5-72b-instruct
```

For hackathon execution and cost-controlled demo runs, the same code path can also operate with Qwen Cloud fast-inference models such as:

```text
qwen3.6-flash
qwen-turbo
qwen-plus
```

The model is not hardcoded in application logic. Judges can reproduce the system by setting the model ID available in their Qwen Cloud account or Token Plan entitlement.

---

## Architecture Overview

The hackathon version is a compact, auditable backend that demonstrates the core SignalReview agent society without exposing the commercial production stack.

```text
Vercel Client / Demo Surface
        |
        | HTTPS / JSON payload
        v
Alibaba Cloud ECS Backend
8.220.101.4
FastAPI + Uvicorn + systemd
        |
        | /api/review-live-match
        v
SignalReview Agent Runtime
Statistician -> Skeptic -> Upside Scout -> Orchestrator
        |
        | OpenAI-compatible request
        v
Qwen Cloud / DashScope Model API
https://dashscope-intl.aliyuncs.com/compatible-mode/v1
or Token Plan routing endpoint
        |
        v
Structured dashboard-ready JSON
```

### Data Layer

The public hackathon repository accepts sports context through a provider-agnostic payload. This keeps the demo safe and reproducible while allowing integration with external football data providers.

The intended production-style data flow is:

```text
API-Football-compatible match feed
        |
        v
provider_snapshot / recent_form / quant_context / news_context
        |
        v
SignalReview live_match_processor.py
        |
        v
Qwen-powered multi-agent debate
```

This design means the public API can be tested with static payloads while still matching the data shape needed for live sports-provider integrations.

---

## API Surface

The FastAPI app exposes a minimal contract suitable for live demo verification.

### `GET /api/health`

Confirms that the ECS service, Uvicorn process, and FastAPI router are alive.

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "signalreview-alibaba-qwen-hackathon",
  "runtime": "fastapi"
}
```

### `GET /api/qwen-health`

Confirms that the Qwen runtime configuration is loaded without revealing the full API key.

```bash
curl http://127.0.0.1:8000/api/qwen-health
```

Example response:

```json
{
  "status": "configured",
  "model": "qwen3.6-flash",
  "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
  "host": "dashscope-intl.aliyuncs.com",
  "has_api_key": true,
  "api_key_prefix": "sk-...",
  "timeout_seconds": 45.0
}
```

### `GET /api/qwen-models`

Probes the configured Qwen-compatible `/models` endpoint and returns provider visibility for debugging model entitlement issues.

```bash
curl http://127.0.0.1:8000/api/qwen-models
```

This endpoint is diagnostic-only. It is useful when a model appears in the provider catalog but chat completions require separate activation, Token Plan routing, or billing entitlement.

### `POST /api/review-live-match`

Runs the multi-agent sports-intelligence review.

```bash
curl -X POST http://127.0.0.1:8000/api/review-live-match \
  -H 'Content-Type: application/json' \
  -d '{
    "match_id": "world-cup-2026-r16-canada-morocco-53452511",
    "home_team": "Canada",
    "away_team": "Morocco",
    "competition": "FIFA World Cup 2026 - Round of 16",
    "kickoff_utc": "2026-07-04T17:00:00Z",
    "venue": "NRG Stadium, Houston",
    "provider_snapshot": {
      "match_status": "complete",
      "score": "Canada 0-3 Morocco",
      "lineups": "unavailable",
      "market_evidence": "unavailable"
    },
    "recent_form": {},
    "quant_context": {},
    "news_context": {}
  }'
```

The response is a structured JSON review with:

- `confidence_band`;
- `value_edge` as a responsible-use scenario label;
- `risk_flags`;
- `agents[]` with individual agent summaries;
- `claim_tags`;
- `missing_data`;
- `orchestrator_verdict`;
- `transparency_notes`;
- `responsible_use_note`.

---

## Security & IP Protection

This repository was prepared for public judging and safe open-source inspection.

### What is intentionally excluded

The public hackathon repo does **not** contain:

- Supabase schema migrations;
- Supabase service-role keys;
- production database URLs;
- commercial SignalReview.co backend services;
- payment or billing logic;
- user authentication contracts;
- proprietary artifact pipelines;
- private model calibration data;
- production secrets.

### Shadow Calibration Principle

SignalReview AI uses a public-safe **Shadow Calibration** pattern for this hackathon build.

Instead of shipping commercial calibration tables or production datasets, the demo runtime calibrates its response boundaries at request time from the provided match context. The agents receive only the submitted payload and must preserve missing evidence as explicit diagnostics.

That gives judges a working multi-agent product demonstration while protecting the commercial IP surface.

### Responsible Sports Intelligence

The model prompt and sanitizer enforce a strict responsible-use boundary.

The application rejects or neutralizes language associated with:

- guaranteed outcomes;
- betting certainty;
- bookmaker recommendations;
- staking instructions;
- fake ROI;
- financial advice.

SignalReview AI is an intelligence terminal, not a gambling assistant.

---

## Repository Structure

```text
.
├── live_match_processor.py   # Qwen-powered multi-agent review engine
├── live_routes.py            # FastAPI routes and diagnostic endpoints
├── main.py                   # FastAPI application entrypoint
├── deploy.sh                 # Alibaba ECS deployment script
├── requirements.txt          # Python runtime dependencies
├── .env.example              # Safe environment template
├── LICENSE                   # MIT license
└── README.md                 # Project documentation
```

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/moneyparking/Signalreview-Alibaba-Qwen.git
cd Signalreview-Alibaba-Qwen
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment

Create `.env`:

```bash
cp .env.example .env
```

For standard Qwen Cloud / pay-as-you-go keys:

```env
DASHSCOPE_API_KEY=sk-your-key-here
QWEN_MODEL=qwen3.6-flash
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
ALLOWED_ORIGINS=*
SIGNALREVIEW_ENV=hackathon
PORT=8000
```

For Token Plan hackathon keys with prefix `sk-sp-`:

```env
DASHSCOPE_API_KEY=sk-sp-your-token-plan-key-here
QWEN_MODEL=qwen3.6-flash
QWEN_BASE_URL=https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
ALLOWED_ORIGINS=*
SIGNALREVIEW_ENV=hackathon
PORT=8000
```

### 5. Run the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Verify locally

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/qwen-health
```

---

## Alibaba Cloud ECS Deployment

The project includes a production-style deployment script for a single ECS instance.

### Current live backend

```text
Alibaba Cloud ECS Public IP: 8.220.101.4
Health route: http://8.220.101.4:8000/api/health
API docs: http://8.220.101.4:8000/docs
```

### Deploy with `deploy.sh`

```bash
export DASHSCOPE_API_KEY='your-qwen-cloud-key'
export QWEN_MODEL='qwen3.6-flash'
export QWEN_BASE_URL='https://dashscope-intl.aliyuncs.com/compatible-mode/v1'
export SERVER_PUBLIC_IP='8.220.101.4'
export PORT='8000'

sudo -E bash deploy.sh
```

For Token Plan keys:

```bash
export DASHSCOPE_API_KEY='your-sk-sp-token-plan-key'
export QWEN_MODEL='qwen3.6-flash'
export QWEN_BASE_URL='https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1'

sudo -E bash deploy.sh
```

### What `deploy.sh` does

The deployment script is intentionally simple and auditable.

It performs the following steps:

1. validates that it is running as root;
2. validates that `DASHSCOPE_API_KEY` is present;
3. installs system dependencies: Git, Python, venv, pip, curl;
4. clones or hard-resets the repository into `/opt/signalreview-qwen`;
5. creates a Python virtual environment;
6. installs `requirements.txt`;
7. writes a locked-down `.env` file with `chmod 600`;
8. creates a `systemd` unit named `signalreview-qwen`;
9. starts and enables the service;
10. runs a local health check.

### systemd service

The deployed service runs as:

```text
signalreview-qwen.service
```

Useful commands:

```bash
systemctl status signalreview-qwen --no-pager --full
journalctl -u signalreview-qwen -n 120 --no-pager
systemctl restart signalreview-qwen
```

---

## Deployment & Verification Log

The backend has been verified on Alibaba Cloud ECS using the following operational checks.

### Service status

```bash
systemctl status signalreview-qwen --no-pager --full
```

Expected runtime signature:

```text
Active: active (running)
ExecStart=/opt/signalreview-qwen/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Uvicorn running on http://0.0.0.0:8000
```

### Health route

```bash
curl http://127.0.0.1:8000/api/health
```

Expected:

```json
{
  "status": "ok",
  "service": "signalreview-alibaba-qwen-hackathon",
  "runtime": "fastapi"
}
```

### Qwen runtime route

```bash
curl http://127.0.0.1:8000/api/qwen-health
```

Expected:

```json
{
  "status": "configured",
  "model": "qwen3.6-flash",
  "has_api_key": true
}
```

### Public verification

```bash
curl http://8.220.101.4:8000/api/health
```

This confirms that the public ECS deployment is reachable for judges and demo reviewers.

---

## Qwen Cloud Integration Notes

The application uses the OpenAI-compatible request format:

```text
POST /compatible-mode/v1/chat/completions
```

Runtime configuration is environment-driven:

```text
DASHSCOPE_API_KEY
QWEN_MODEL
QWEN_BASE_URL
QWEN_TIMEOUT_SECONDS
```

The implementation intentionally supports both standard Qwen Cloud routing and Token Plan routing.

| Key type | Base URL |
| --- | --- |
| `sk-...` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| `sk-sp-...` | `https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1` |

Do not mix key type and base URL. If a model is visible in `/models` but `/chat/completions` returns `AccessDenied.Unpurchased`, the model requires activation, entitlement, or a different Token Plan route.

---

## Example Output Shape

```json
{
  "match_id": "world-cup-2026-r16-canada-morocco-53452511",
  "match": "Canada vs Morocco",
  "competition": "FIFA World Cup 2026 - Round of 16",
  "confidence_band": "Low",
  "value_edge": "Scenario review only",
  "risk_flags": [
    "lineups_unavailable",
    "market_evidence_unavailable"
  ],
  "agents": [
    {
      "agent_name": "Statistician",
      "summary": "The supplied score context is available, but deeper provider features are absent.",
      "dashboard_bullets": [
        "Score state is supplied by the request payload.",
        "Lineup and market evidence are explicitly unavailable."
      ],
      "missing_data": [
        "lineups",
        "verified player events",
        "market evidence"
      ],
      "claim_tags": {
        "score_context": "data_backed",
        "tactical_detail": "unavailable"
      }
    }
  ],
  "orchestrator_verdict": "The review is suitable for transparent post-match intelligence, not certainty claims.",
  "transparency_notes": [
    "Unavailable provider fields are preserved as missing data, not filled by the model."
  ],
  "responsible_use_note": "SignalReview provides structured sports intelligence and transparent reasoning. It does not provide betting predictions, gambling advice, bookmaker recommendations, staking instructions, certainty, guarantees, or financial advice.",
  "raw_model": "qwen3.6-flash"
}
```

---

## Judging Relevance

### Innovation & AI Creativity

SignalReview AI applies a multi-agent debate pattern to sports intelligence instead of simple prompt completion. Each agent has a distinct epistemic function and the Orchestrator resolves the final state.

### Technical Depth & Engineering

The project demonstrates:

- FastAPI service boundaries;
- Qwen Cloud OpenAI-compatible integration;
- model entitlement diagnostics;
- schema validation with Pydantic;
- deployment automation with `systemd`;
- safe environment isolation;
- missing-data preservation;
- responsible-use output filtering.

### Problem Value & Impact

The product addresses a real problem: sports-analysis products often overstate confidence. SignalReview AI shows how to build a safer, more transparent intelligence terminal for sports organizations, analysts, media teams, and fan-facing data products.

### Presentation & Documentation

This repository includes:

- public MIT license;
- local run instructions;
- Alibaba ECS deployment instructions;
- API route documentation;
- model-routing notes;
- security and IP-protection notes;
- reproducible smoke-test commands.

---

## License

MIT License.

Participants, judges, and reviewers may inspect, clone, and run this repository for hackathon evaluation.

---

## Maintainer

Built by the SignalReview team for the **Global AI Hackathon Series with Qwen Cloud**.

Repository:

```text
https://github.com/moneyparking/Signalreview-Alibaba-Qwen
```
