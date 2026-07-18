# SignalReview Qwen Judge Verification Pack - Source

**Document:** `SignalReview_Qwen_Judge_Verification_Pack.pdf`  
**Version:** 1.0  
**Verification date:** 2026-07-18  
**Issued timestamp used on the pack:** 2026-07-15 18:26:00 UTC  
**Track:** Track 3 - Agent Society

## Executive verification statement

SignalReview converts fragmented sports-evidence signals into a structured adversarial multi-agent review while preserving provenance, missing-data visibility, and responsible decision support. The public hackathon repository isolates the Qwen Agent Society from the private commercial platform.

## Judge links

- Public repository: https://github.com/moneyparking/Signalreview-Alibaba-Qwen
- Devpost: https://devpost.com/software/signalreview-co
- Public demo video: https://youtu.be/3GKHrsXoqII
- Judge-accessible UI: https://signalreview.co/dashboard/demo
- Official rules: https://qwencloud-hackathon.devpost.com/rules
- Alibaba ECS deployment manifest: https://github.com/moneyparking/Signalreview-Alibaba-Qwen/blob/main/deploy.sh
- MIT License: https://github.com/moneyparking/Signalreview-Alibaba-Qwen/blob/main/LICENSE

## Current truth and evidence mapping

| Claim | Verified owner | Evidence |
| --- | --- | --- |
| Public open-source project | GitHub | Public repository, root MIT License |
| Alibaba deployment path | GitHub + supplied console screenshots | `deploy.sh`; redacted ECS evidence from Germany (Frankfurt) |
| Current isolated data plane | Source code | `forensic_data_broker.py`, `live_match_processor.py`, `live_routes.py` |
| Qwen role | Source code | Four sequential OpenAI-compatible `/chat/completions` calls, server-side configuration |
| Missing-data boundary | Source code + public UI | Missing domains reduce confidence; current demo shows unavailable states |
| Working demo evidence | Uploaded control frames | 1920x1080 frames through 01:39; fresh remote Qwen call not independently replayed in this session |

## Active data sources and states

1. **Request-supplied provider snapshot and recent form** - treated as observed input only when present. The isolated public runtime does not fetch a provider.
2. **Request-supplied deterministic quant context** - calculated upstream; Qwen may interpret but may not create or alter metrics.
3. **Golden Dataset** - non-live calibration context only. It cannot be described as live fixture truth or outcome accuracy.
4. **Qualitative news context** - request-supplied labels only; no invented injuries or private news.
5. **Content-addressed in-process cache** - reuses equivalent packets and performs zero provider network calls.
6. **API-Football** - disabled and not used by the isolated public Qwen request path.

## Four-agent contract

- **Statistician:** three exact evidence-bound claims.
- **Skeptic:** K1/K2/K3 directly challenge S1/S2/S3 through shared evidence references.
- **Upside Scout:** primary scenario, alternate scenario, and observable invalidation.
- **Orchestrator:** classifies every specialist claim exactly once as accepted, rejected, or unresolved; publishes confidence band and risk flags.

Qwen interprets supplied evidence and resolves disagreement. Deterministic code owns evidence rows, numeric values, missing-data state, contract validation, and safe recovery.

## Judge walkthrough record

**Public URL tested:** https://signalreview.co/dashboard/demo  
**Verification date:** 2026-07-18  
**Reference video viewport:** 1920x1080  
**Workflow:** public demo -> Match Board -> AI Debate -> evidence / missing states -> Orchestrator verdict.

### Test A - supported scenario

- Public UI loaded without login: **PASS**.
- Statistician, Skeptic, Upside Scout and Orchestrator visibly differentiated: **PASS**.
- Captured Qwen hackathon walkthrough reaches Broker, Evidence and Verdict panels: **PASS (captured evidence)**.
- Fresh Qwen network execution from the isolated public API: **UNAVAILABLE** because the Alibaba ECS resource is stopped and no current public API endpoint was exposed for this verification session.
- Agent text remains responsible-use framed and avoids certainty claims: **PASS**.

### Test B - incomplete/conflicting evidence

The current public demo visibly reports Quant Layer `Unavailable`, provider evidence missing, market and lineup evidence unavailable, and unknown freshness states. Agent text preserves those limits. **PASS for visible missing-data behavior; Qwen network execution unavailable.**

## Material submission mismatch found

The current Devpost description still states that the broker sits between live providers `(API-Football)` and the runtime and names a fixed Singapore/qwen-plus deployment. Captured video-era UI frames also contain legacy API-Football source labels. Current public source proves a different boundary: request-supplied inputs, zero provider network calls, environment-configured Qwen model, and supplied deployment evidence from Germany (Frankfurt).

Apply `DEVPOST_COPY_PATCH.md` before the deadline and disclose that video-era API-Football labels are historical presentation evidence, not the current isolated request path.

## Update instructions

1. Regenerate redacted screenshots from the original private captures; never commit originals.
2. Re-run the PDF generator and QA commands documented in the repository PR.
3. Replace the PDF and update its SHA-256.
4. Keep current source and Devpost description synchronized; do not reintroduce API-Football as an active isolated-runtime source.
