# 5-minute-only strategy replay (offline)

This tool is deliberately isolated from the live recommendation runner. It does not change `Entry/main.py`, disable live filters, or place orders.

## What it compares

- **15m+5m baseline:** requires 15-minute and 5-minute direction to agree.
- **5m-only experiment:** uses the 5-minute direction without the 15-minute alignment requirement.
- Both variants keep the same price-action direction check, mandatory-check flag, and minimum score (80 by default).
- Signals are generated from a completed bar and entered at the following bar's option open, avoiding same-bar look-ahead.
- Exit simulation uses the selected option's OHLC and supplied structural SL/target. If SL and target both fall inside one bar, the simulator counts SL first (conservative).
- Results include eligible signals, simulated trades, win rate, additional 5m-only signals, and favourable/adverse excursion.

## Required input CSV

One row per completed 5-minute candle. Required headers:

`timestamp,direction_15m,direction_5m,price_action_signal,score,mandatory_checks_pass,ce_open,ce_high,ce_low,ce_close,ce_sl,ce_target,pe_open,pe_high,pe_low,pe_close,pe_sl,pe_target`

- Direction values: `BULLISH`, `BEARISH`, or neutral/blank.
- `mandatory_checks_pass`: true/false. It must represent the same non-timeframe veto/risk-independent gates for both strategies.
- CE/PE OHLC are option premium candles for that timestamp.
- SL/target must be structural levels known at signal time; do not calculate them using future candles.
- For an exact baseline comparison, supply the actual 15m label aligned to each 5m close (not a future 15m close).
- Keep the CSV to one session/instrument at a time or add session/instrument grouping before combining datasets; don't let the replay cross expiry/session boundaries.

## Run

```powershell
python -m unittest discover -s tests -p test_timeframe_replay.py -v
python tools/timeframe_replay.py path\to\historical_5m_replay.csv --lookahead 12 --out reports\5m_replay_results.json
```

## Important limitation

No historical candle dataset was available to this run, so there are no honest real-market win-rate or missed-move numbers yet. The tests use synthetic rows to verify replay mechanics only. Do not switch live logic based on synthetic results. Include brokerage, bid/ask spread, slippage, rejected quotes, and realistic option candles before deciding whether 5m-only improves performance.
