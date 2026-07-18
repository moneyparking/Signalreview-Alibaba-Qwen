# Devpost Copy Patch - Provider-Backed Judge Runtime

**Apply only after the deployed runtime passes the judge checks.**

## Replace the data-plane description with

> SignalReview runs an isolated FastAPI backend on Alibaba Cloud ECS. A quota-safe server-side API-Football adapter discovers current fixtures and hydrates fixture identity, recent form, and H2H observations. A deterministic evidence layer calculates lambda, 1/X/2, O2.5, BTTS, evidence completeness, and confidence before Qwen inference. These calculations are model estimates, not API-Football facts. The Forensic Data Broker preserves provenance and missing domains, then four sequential Qwen roles - Statistician, Skeptic, Upside Scout, and Orchestrator - interpret and adjudicate the same bounded evidence packet.

## Replace the deployment description with

> The judge backend runs on Alibaba Cloud ECS in Germany (Frankfurt) and calls Qwen through the Alibaba Cloud Model Studio OpenAI-compatible API. The model, endpoint, and provider credentials remain server-side. The deployment manifest is public in `deploy.sh`, and the judge environment is kept online through the judging period.

## Add this safety disclosure

> Qwen does not create provider facts, odds, injuries, line movement, private news, deterministic metrics, ROI, accuracy, or outcomes. Missing lineups, external market references, injuries, and news remain visible when unavailable and can only reduce the confidence ceiling.

## Testing instructions

```text
Public UI: https://signalreview.co/dashboard/demo
Public repository: https://github.com/moneyparking/Signalreview-Alibaba-Qwen
Demo video: https://youtu.be/3GKHrsXoqII

Open the public UI without authentication. Select a current API-Football-backed fixture and click Run Qwen Agent Society / ENGAGE. Confirm that Statistician, Skeptic, Upside Scout, and Orchestrator produce distinct outputs and that accepted, rejected, and unresolved claims remain visible.

Then select the incomplete-evidence scenario. Confirm that confidence is constrained, unresolved disagreement is preserved, and missing facts are not filled.
```

## Built With

Qwen Cloud, Alibaba Cloud, ECS, FastAPI, Python, Pydantic, httpx, Uvicorn, API-Football.
