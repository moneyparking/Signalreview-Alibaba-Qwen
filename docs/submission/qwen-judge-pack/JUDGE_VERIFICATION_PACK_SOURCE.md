# SignalReview Qwen Judge Verification Pack - Source

**Document:** `SignalReview_Qwen_Judge_Verification_Pack.pdf`  
**Source version:** 1.2  
**Track:** Track 3 - Agent Society

## Executive verification statement

SignalReview converts a bounded football evidence packet into a structured adversarial Qwen Agent Society review while preserving provenance, missing-data visibility, and responsible decision support.

The judge-accessible UI pins one immutable pre-match **Qwen Judge Reference Review**. It is retained through the judging window so the complete workflow remains reproducible even when a live provider is unavailable. The row is not described as a live match, and no post-match result enters the packet.

## Judge links

- Public repository: `https://github.com/moneyparking/Signalreview-Alibaba-Qwen`
- Devpost: `https://devpost.com/software/signalreview-autonomous-multi-agent-ai`
- Public demo video: `https://youtu.be/3GKHrsXoqII`
- Judge-accessible UI: `https://signalreview.co/dashboard`
- Official rules: `https://qwencloud-hackathon.devpost.com/rules`
- Alibaba ECS deployment implementation: `https://github.com/moneyparking/Signalreview-Alibaba-Qwen/blob/main/deploy.sh`
- MIT License: `https://github.com/moneyparking/Signalreview-Alibaba-Qwen/blob/main/LICENSE`

## Canonical public journey

```text
Match Board
  → Qwen Judge Reference Review
  → ENGAGE Qwen Agent Society
  → immutable pre-match evidence packet
  → 30-row Quant Passport
  → Qwen Statistician
  → Qwen Skeptic
  → Qwen Upside Scout
  → Qwen Orchestrator
  → evidence contract + coverage + confidence ceiling + verdict
```

Expected current reference result:

- registry: 30/30 rows retained;
- validated evidence coverage: 15/30 rows;
- evidence contract: PARTIAL;
- confidence ceiling: LOW;
- four ordered Qwen roles;
- explicit missing market, confirmed-lineup, injury, travel, and provider-observed domains;
- no outcome probability, lambda, Value Edge, ROI, accuracy, or certainty assertion.

## Evidence classes

| Class | Meaning | Current reference examples |
| --- | --- | --- |
| Official fixture identity | Hash-bound tournament identity | teams, competition, round, original kickoff, venue |
| Historical observed | Primary-source tournament history | form sequence, goals, rest/workload, H2H context |
| Deterministic derived | Reproducible calculation from cited inputs | form strength, attack/defence deltas, sample depth, evidence diagnostics |
| Estimated projection | Clearly non-observed context | possible starting XI, weather forecast |
| Blocked / unavailable | Inputs that remain null | market, confirmed lineups, injuries, live provider statistics, travel |

Historical and projected evidence never becomes provider-observed evidence and never raises the Low confidence ceiling.

## Four-agent contract

- **Statistician:** synthesizes evidence-bound drivers and counter-drivers using structured references.
- **Skeptic:** challenges the same evidence rows and applies the data-scarcity ceiling.
- **Upside Scout:** separates primary and alternate scenarios, observable triggers, and invalidation conditions.
- **Orchestrator:** classifies specialist findings as accepted, rejected, or unresolved and publishes the bounded verdict.

## Match Board universe

The release contains two distinct fixture modes:

1. **Judge reference** — one pinned evidence-rich reference with ENGAGE enabled.
2. **Schedule only** — versioned official upcoming identities for discovery; ENGAGE is disabled until a fixture-specific packet is bound.

Schedule-only rows never reuse the reference fixture's statistics, lineups, weather, Quant Passport values, or Qwen output.

## Qwen and Alibaba evidence mapping

| Claim | Evidence |
| --- | --- |
| Qwen Cloud model use | Runtime source, validated UI response, redacted Model Studio evidence |
| Four-agent society | `live_match_processor.py`, role contracts, UI role outputs |
| Alibaba deployment implementation | Public `deploy.sh` and redacted Alibaba console evidence |
| Open-source submission | Public repository plus root MIT License |
| Reproducibility | exact dependencies, tests, local run instructions, runtime verifier |
| Missing-data safety | blocked/null registry rows and visible Low confidence ceiling |

The public repository contains an isolated ECS-deployable implementation and optional API-Football adapter. A current ECS uptime or provider-availability claim must be supported by a fresh runtime check; deployment code alone is not treated as uptime proof.

## Required judge test

1. Open `https://signalreview.co/dashboard` in a private/incognito window.
2. Confirm the first row is labelled `QWEN JUDGE REFERENCE` or `Qwen Judge Reference Review`.
3. Confirm it is Spain vs Argentina and is labelled as a reference review rather than live.
4. Click `ENGAGE Qwen Agent Society`.
5. Wait for the processing rail to publish.
6. Confirm the four roles appear in order: Statistician, Skeptic, Upside Scout, Orchestrator.
7. Confirm the UI reports Qwen reasoning validated/ready.
8. Confirm Quant Passport registry 30, coverage 15/30, Evidence Contract PARTIAL, Confidence Ceiling LOW.
9. Confirm missing domains remain visible and no unavailable fact is filled.
10. Inspect one official UEFA schedule-only row and confirm it is visibly distinct and cannot run an inherited debate.

## Video-alignment statement

The current judge journey preserves the functionality demonstrated in the submitted video:

- structured Match Board selection;
- deterministic evidence normalization;
- a retained 30-row Quant Passport;
- four adversarial Qwen roles;
- an Orchestrator verdict;
- visible evidence provenance, missing domains, and bounded confidence.

The current release is more explicit than the video about evidence completeness: it shows validated coverage separately from registry size and does not describe the retained reference as live.

## Production acceptance evidence required before PASS

Do not mark the submission runtime PASS until all are verified against the deployed commit:

- public deployment fingerprint matches the merged release;
- Match Board contains the pinned reference and official schedule rows;
- reference ENGAGE returns Qwen ready/validated;
- four roles and Orchestrator verdict render through the UI;
- coverage and confidence ceiling match the response contract;
- schedule-only rows remain fail-closed;
- public repository, video, Devpost copy, screenshots, and PDF describe the same journey.

## PDF regeneration

After production acceptance:

1. capture a fresh incognito Match Board screenshot;
2. capture the processing rail showing Qwen validation;
3. capture 15/30 evidence coverage and Low ceiling;
4. capture the four roles and verdict;
5. record the deployed commit fingerprint;
6. regenerate `SignalReview_Qwen_Judge_Verification_Pack.pdf` from this source;
7. upload it to Devpost Additional info and verify links/captions at 100%.
