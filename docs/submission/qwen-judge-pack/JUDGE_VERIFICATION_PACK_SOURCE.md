# SignalReview Qwen Judge Verification Pack - Source

**Document:** `SignalReview_Qwen_Judge_Verification_Pack.pdf`  
**Source version:** 1.1  
**Track:** Track 3 - Agent Society

## Executive verification statement

SignalReview converts fragmented sports-evidence signals into a structured adversarial Qwen Agent Society review while preserving provenance, missing-data visibility, and responsible decision support. The public hackathon backend is isolated from the private commercial platform and is deployable on Alibaba Cloud ECS.

## Judge links

- Public repository: https://github.com/moneyparking/Signalreview-Alibaba-Qwen
- Devpost: https://devpost.com/software/signalreview-co
- Public demo video: https://youtu.be/3GKHrsXoqII
- Judge-accessible UI: https://signalreview.co/dashboard/demo
- Official rules: https://qwencloud-hackathon.devpost.com/rules
- Alibaba ECS deployment manifest: https://github.com/moneyparking/Signalreview-Alibaba-Qwen/blob/main/deploy.sh
- MIT License: https://github.com/moneyparking/Signalreview-Alibaba-Qwen/blob/main/LICENSE

## Current architecture and evidence mapping

| Claim | Owner | Evidence |
| --- | --- | --- |
| Public open-source project | GitHub | Public repository and root MIT License |
| Alibaba deployment path | GitHub + console evidence | `deploy.sh`; redacted ECS evidence from Germany (Frankfurt) |
| Live provider adapter | Source code | `api_football_provider.py`, `/api/provider-health`, `/api/judge-fixtures` |
| Deterministic evidence and quant | Source code | `api_football_provider.py`, `forensic_data_broker.py` |
| Qwen Agent Society | Source code | `live_match_processor.py`, four sequential `/chat/completions` passes |
| Missing-data boundary | Source and UI | Unavailable domains remain visible and reduce the confidence ceiling |

## Active data plane

1. **API-Football live provider adapter** - server-side only. The key never reaches the browser.
2. **Quota budget and cache** - default application budget is 80 provider calls per UTC day with a 15-minute process cache. One uncached provider-backed review uses four bounded calls.
3. **Observed fixture evidence** - fixture identity, recent form, and H2H are provider observations.
4. **Deterministic quant context** - lambda, 1/X/2, O2.5, BTTS, evidence completeness, and confidence are calculated before Qwen. They are model estimates, not provider facts.
5. **Missing domains** - official lineups, external market reference, verified injuries, and private news remain unavailable unless actually supplied.
6. **Qwen role** - Qwen interprets the evidence packet and resolves disagreement. It cannot create provider facts or deterministic metrics.
7. **Request-supplied path** - remains available for reproducible adversarial and incomplete-evidence tests.
8. **Golden Dataset** - non-live calibration only; never live fixture truth or outcome accuracy.

## Four-agent contract

- **Statistician:** evidence-bound claims using exact structured values.
- **Skeptic:** direct challenges through shared evidence rows.
- **Upside Scout:** primary scenario, alternate scenario, triggers, and invalidation.
- **Orchestrator:** accepted / rejected / unresolved classification, confidence ceiling, risk flags, and final responsible-use verdict.

## Required judge tests after deployment

### Test A - live supported fixture

1. Open `https://signalreview.co/dashboard/demo` without login.
2. Confirm the selected row is labelled `API-Football live provider` or equivalent.
3. Click `Run Qwen Agent Society` / `ENGAGE`.
4. Confirm four distinct agent outputs appear.
5. Confirm the response identifies Alibaba Cloud ECS and Qwen reasoning.
6. Confirm provider evidence, deterministic estimates, and missing domains remain separately labelled.

### Test B - incomplete evidence

1. Select the controlled incomplete-evidence scenario or a live fixture without lineups/market evidence.
2. Run the review.
3. Confirm confidence is constrained, unresolved disagreement remains visible, and no missing fact is filled.

## Deployment verification requirements

The final submission evidence must show:

- ECS is running and `/api/health` returns `ok`;
- `/api/qwen-health` is configured;
- `/api/qwen-models` can see the configured Qwen model;
- `/api/provider-health` is configured without exposing the key;
- `/api/judge-fixtures` returns current provider fixture rows;
- `/api/review-provider-fixture` returns the complete four-agent contract;
- the public UI completes the same workflow in incognito.

Do not mark these runtime checks PASS until they are executed against the deployed judge environment.

## Update instructions

1. Start or redeploy the Alibaba ECS backend with server-side Qwen and API-Football variables.
2. Configure the SignalReview web deployment with the server-only ECS base URL.
3. Run both judge tests in desktop and mobile viewports.
4. Regenerate the Judge Verification Pack PDF from the verified runtime evidence.
5. Update Devpost copy so API-Football is described as an active server-side adapter and deterministic estimates are not described as provider facts.
