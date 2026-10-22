# JARVIS Dashboard Phases 1–8

This plan extends the existing dashboard without replacing its layout or deterministic trading flow. All panels are read-only; the browser never places or modifies broker orders. Missing source data is displayed as unavailable rather than fabricated.

## Phase 1 — Holographic JARVIS Core
Existing dashboard/agentic_panel.js: bias-aware core, score/review display, neutral fallback, reduced-motion support. Startup publication and Windows visual verification remain runtime acceptance checks.

## Phase 2 — SENSEX / option heatmap
dashboard/jarvis_phases.js renders actual option-chain strike/type, premium, premium change, OI and volume. No data means an explicit unavailable state.

## Phase 3 — Signal timeline
Displays existing 15m/5m alignment, 1m confirmation, deterministic decision, and structure from live_state.json; does not recalculate or override them.

## Phase 4 — Order-flow view
Displays actual available bid/ask prices and quantities and a simple visible quantity imbalance. Missing depth is not synthesized; depth is not a standalone entry signal.

## Phase 5 — Historical replay
Allows selection/navigation through trade records present in the published state. This is a historical trade-record viewer, not tick/candle replay. True candle replay requires a backend-published historical dataset.

## Phase 6 — Voice alerts
Browser speech is opt-in, off by default, and deduplicated per decision/strike/expiry/score key. It only announces recommendations; manual orders remain required.

## Phase 7 — Risk and probability
Displays score, estimated per-lot entry-to-SL risk, reward/risk, and the ₹1,000 reference cap. It does not label entry score as probability; a win rate is shown only when a backend-published historical statistic exists.

## Phase 8 — System health
Displays available snapshot freshness, market status, active-trade lock, refresh interval and Telegram status when the backend publishes it. It does not claim Telegram is healthy when no status field exists.

## Acceptance and limitations
- Automated Node tests cover normalization, risk math, health freshness and heatmap direction.
- GitHub Actions validates the new browser module and runs the existing project tests that do not require live broker credentials.
- Browser rendering, Windows path/server behavior, real broker depth, voice permissions and live Telegram delivery still require runtime validation.
- Do not commit .env, tokens, access tokens, or generated live-state files.
