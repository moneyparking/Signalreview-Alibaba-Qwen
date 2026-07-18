# Devpost Copy Patch - Current Truth Alignment

**Status:** REQUIRED BEFORE DEADLINE  
**Reason:** The live Devpost description contains two material mismatches with current public source and supplied deployment proof.

## Patch 1 - data source

**Before**

> Forensic Data Broker: A hardened data-ingestion layer (`forensic_data_broker.py`) that acts as a secure buffer between live providers (API-Football) and the agent runtime.

**After**

> Forensic Data Broker: A public-safe evidence adapter that transforms request-supplied provider snapshots and recent-form context, request-supplied deterministic quant context, qualitative news context, and non-live Golden Dataset calibration into an auditable packet. The isolated request path performs zero external provider calls and reuses equivalent packets through a content-addressed in-process cache.

## Patch 2 - Qwen model and deployment location

**Before**

> ...orchestrated sequentially via the premium qwen-plus model deployed through Singapore Model Studio compatible endpoints.

**After**

> ...orchestrated sequentially through the Alibaba Cloud Model Studio OpenAI-compatible API. The enabled Qwen model and endpoint are environment-configured and remain server-side. Supplied deployment evidence is for Alibaba Cloud ECS in Germany (Frankfurt); the paid ECS resource is currently stopped for cost containment.

## Patch 3 - video-era source labels

**Observed**

Captured demo frames contain legacy API-Football source attribution from the earlier presentation layer.

**Disclosure to add**

> The recorded demo contains historical API-Football labels from the earlier UI presentation. The current isolated public Qwen runtime performs zero external provider calls; provider observations are request-supplied and API-Football is disabled in that request path.

## Recommended complete replacement description

## Inspiration

Sports intelligence is commonly split between opaque quantitative pages and generic AI summaries that do not preserve provenance or uncertainty. SignalReview was updated during the hackathon to demonstrate a public-safe, zero-fabrication Qwen Agent Society: specialized agents cross-examine the same deterministic evidence packet instead of independently inventing facts.

## What it does

SignalReview turns structured match context into an adversarial four-agent review:

- **Statistician** publishes exact evidence-bound claims.
- **Skeptic** challenges each Statistician claim through the same evidence row.
- **Upside Scout** separates the primary scenario, alternate scenario, and observable invalidation.
- **Orchestrator** classifies every specialist claim as accepted, rejected, or unresolved and publishes a confidence band, risk flags, and a responsible-use verdict.

Missing, stale, or unavailable inputs remain visible and can only constrain confidence.

## How we built it

The public repository is an isolated Python/FastAPI implementation aligned with Alibaba Cloud and Qwen Cloud:

1. **Forensic Data Broker** - adapts request-supplied provider snapshots and recent-form context, request-supplied deterministic quant context, qualitative news context, and a non-live Golden Dataset calibration snapshot. The isolated request path performs **zero external provider calls** and reuses equivalent packets through a content-addressed in-process cache.
2. **Qwen Agent Society** - four sequential, role-separated passes use the Alibaba Cloud Model Studio OpenAI-compatible API. The Qwen model and endpoint are selected through server-side environment variables and are not hardcoded or exposed to the browser.
3. **Contract validation** - exact numeric grounding, structured evidence references, paired Skeptic challenges, complete Orchestrator classification, forbidden-claim scanning, bounded repair attempts, and deterministic contract-safe fallback.
4. **Alibaba Cloud deployment** - the FastAPI service was deployed and verified on Alibaba Cloud ECS in Germany (Frankfurt). The paid ECS resource was later stopped for cost containment. `deploy.sh` reproduces the Ubuntu 22.04 systemd deployment and verifies `/api/health`.

**API-Football is not an active source in this isolated public Qwen runtime.** Provider observations are supplied in the request; Qwen never creates provider facts, injuries, odds, line movement, probabilities, ROI, accuracy, lambdas, or outcomes.

## Challenges we overcame

- Preventing numeric and identifier drift in public agent text.
- Preserving direct adversarial pairing instead of four agents repeating the same summary.
- Keeping missing evidence visible rather than filling gaps.
- Separating a judgeable open-source implementation from private commercial schemas, authentication, billing, datasets, and secrets.
- Providing deterministic safe recovery when model output or transport violates the public contract.

## Testing and judging

Judges can inspect and run the complete public repository, use the exact-version dependencies, call `/api/health`, `/api/qwen-health`, `/api/qwen-models`, and `/api/review-live-match`, and reproduce Alibaba ECS deployment with `deploy.sh`. The attached Judge Verification Pack maps each claim to public source, redacted deployment evidence, the demo workflow, and unresolved checks.

## Responsible use

SignalReview provides structured sports intelligence and transparent reasoning. It does not provide betting predictions, gambling advice, bookmaker recommendations, staking instructions, certainty, guarantees, ROI, accuracy claims, or financial advice.

## Testing instructions replacement

```text
Public UI: https://signalreview.co/dashboard/demo
Public repository: https://github.com/moneyparking/Signalreview-Alibaba-Qwen
Demo video: https://youtu.be/3GKHrsXoqII

The Alibaba Cloud ECS deployment used for verification is currently stopped for cost containment. Judges can reproduce the isolated FastAPI runtime with the exact pinned dependencies and `sudo -E bash deploy.sh` after supplying the documented server-side Qwen environment variables. No login or private commercial credentials are required for repository inspection. The current public UI demonstrates the four roles and honest missing-data states; the video demonstrates the Qwen hackathon workflow. The recorded demo contains historical API-Football labels from the earlier UI presentation. The current isolated public Qwen runtime performs zero external provider calls; provider observations are request-supplied and API-Football is disabled in that request path.
```
