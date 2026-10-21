# JARVIS / Agentic AI Dashboard Integration

## Data flow

1. `Entry/main.py` dispatches an advisory review after recalculating a deterministic setup.
2. `AgenticAI.agent_orchestrator` runs market-intelligence, decision-audit, risk-review and explanation agents asynchronously.
3. The full snapshot is retained at `data/agentic_ai/latest_review.json` and appended to `data/agentic_ai/review_history.jsonl`.
4. A read-only snapshot is atomically published to `dashboard/agentic_review.json`.
5. `dashboard/agentic_panel.js` polls that file every three seconds and renders the latest review on the HTML dashboard. The generated dashboard includes the script through `report/dashboard.py`.

## Safety boundary

- This is an advisory/diagnostic layer only.
- The deterministic trading decision and existing entry/risk gates remain authoritative.
- The agent layer cannot submit, modify, or close broker orders.
- A missing or stale review must not be interpreted as a trade signal. The dashboard shows a waiting/unavailable state instead.
- Local LLM explanation is optional and disabled by default. The deterministic agents still generate a review when Ollama is not enabled.

## Optional local Ollama explanation

To enable the additional local-model explanation, install and start Ollama, pull the configured model (default `qwen2.5:3b`), then set these environment variables in the same environment that starts the trading engine:

```powershell
$env:AGENTIC_AI_OLLAMA_ENABLED = "true"
$env:AGENTIC_AI_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
$env:AGENTIC_AI_OLLAMA_MODEL = "qwen2.5:3b"
python main.py
```

This setting only enables an explanation of the existing review. It does not grant the LLM authority to choose or execute trades.

## Verify

From the repository root:

```powershell
$env:PYTHONPATH = "Entry;.;exit"
python -m pytest -q test/test_agentic_ai.py
python -m compileall -q AgenticAI report
```

Start the normal project runtime and open the served dashboard. After the first completed-candle decision review, the panel should show the review timestamp, deterministic decision status, score, market summary, diagnostic/risk flags, safety note and local-LLM status. If no review exists yet, it should show `WAITING FOR REVIEW`.
