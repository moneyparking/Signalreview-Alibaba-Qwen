# Qwen Devpost Final Operator Checklist

Run immediately before final submission and again before the judging period.

## Public evidence

- [ ] Public repository opens in incognito: https://github.com/moneyparking/Signalreview-Alibaba-Qwen
- [ ] Root MIT License is visible and GitHub About detects it.
- [ ] `deploy.sh` is the Alibaba Cloud proof code link.
- [ ] Architecture diagram is uploaded and linked.
- [ ] Updated `SignalReview_Qwen_Judge_Verification_Pack.pdf` is uploaded under Additional info (<35 MB).

## Alibaba / Qwen runtime

- [ ] Alibaba ECS is running and remains funded through the judging period.
- [ ] `/api/health` returns `status=ok`.
- [ ] `/api/qwen-health` reports configured without exposing credentials.
- [ ] `/api/qwen-models` reports the configured Qwen model visible.
- [ ] `/api/provider-health` reports API-Football configured without exposing the key.
- [ ] `/api/judge-fixtures` returns current provider fixture rows.
- [ ] `/api/review-provider-fixture` returns Statistician, Skeptic, Upside Scout, and Orchestrator.

## Devpost copy

- [ ] Apply the current `DEVPOST_COPY_PATCH.md`.
- [ ] Track field is `Track 3: Agent Society`.
- [ ] Built With tags include Qwen Cloud, Alibaba Cloud, ECS, FastAPI, Python, Pydantic, httpx, Uvicorn, API-Football.
- [ ] Repository URL points to the public Qwen repository.
- [ ] Deployment code URL points directly to `deploy.sh`.
- [ ] Architecture and redacted deployment screenshots are attached.
- [ ] Deterministic estimates are not described as API-Football facts.

## Judge access

- [ ] Demo UI opens without authentication: https://signalreview.co/dashboard/demo
- [ ] Video is public and playable in incognito: https://youtu.be/3GKHrsXoqII
- [ ] Video duration is under 3 minutes.
- [ ] A current provider-backed row can be selected and engaged.
- [ ] Four distinct Qwen agent outputs appear on the public UI.
- [ ] Missing lineups, market evidence, injuries, or news remain visible when unavailable.
- [ ] Controlled incomplete-evidence test preserves unresolved disagreement.
- [ ] No credentials, private hostnames, account IDs, instance IDs, public IPs, or raw provider bodies appear in submission artifacts.

## Personal confirmations

- [ ] Submitter type is correct.
- [ ] All teammates are accepted and listed.
- [ ] Country and age eligibility declarations are accurate.
- [ ] Existing-project start date and submission-period update description are accurate.
- [ ] No post-deadline source changes are planned.

## Visual checks

- [ ] Hero/thumbnail contains no `XLM PROBABILITY` or text drift.
- [ ] Any issued timestamp shown is exactly `2026-07-15 18:26:00 UTC`.
- [ ] PDF links, page numbers, screenshots, and captions render correctly at 100%.
