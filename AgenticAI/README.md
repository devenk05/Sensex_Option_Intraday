# JARVIS Agentic AI

Optional advisory layer for the existing Sensex_Option_Intraday project.

## What it does
- Market Intelligence Agent summarizes outputs from existing deterministic engines.
- Decision Audit Agent flags visible score/decision/confirmation inconsistencies for diagnosis.
- Risk Agent independently reports active-trade and score/risk guardrail flags.
- Explanation Agent creates a compact human-readable diagnostic.
- Optional Ollama local LLM can explain the structured review when explicitly enabled.

## Safety and integration
- This layer runs asynchronously after the existing completed-5-minute decision calculation.
- It never changes `CURRENT_SETUP_DECISION`, the candidate, score, SL, target, or trade registration.
- It never calls Kite order-placement APIs and cannot place/close orders.
- The existing engine remains authoritative; recommendation mode and manual orders are unchanged.
- The LLM is disabled by default, so no new package or API service is required.
- Review files are written to `data/agentic_ai/latest_review.json` and `data/agentic_ai/review_history.jsonl`; project data is already excluded by `.gitignore`.

## Optional local model
Install and start Ollama separately, pull a compatible model such as `qwen2.5:3b`, then set these environment variables before starting the app:

```powershell
$env:AGENTIC_AI_OLLAMA_ENABLED = "true"
$env:AGENTIC_AI_OLLAMA_MODEL = "qwen2.5:3b"
$env:AGENTIC_AI_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
```

If Ollama is absent, the review still works using deterministic agents and continues without affecting trading logic. LLM output is explanatory only, not a trading signal.

## Diagnostics
Search the console for `JARVIS_AGENT_REVIEW:`. The latest structured review is in `data/agentic_ai/latest_review.json`.

## Tests
From the project root:

```powershell
$env:PYTHONPATH = "$PWD;$PWD\Entry;$PWD\exit;$PWD\report"
python -m unittest test.test_agentic_ai
```
