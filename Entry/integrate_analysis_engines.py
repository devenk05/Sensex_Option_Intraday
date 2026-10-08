from pathlib import Path

path = Path("main.py")
text = path.read_text(encoding="utf-8-sig")

imports = [
    "from confluence_engine import calculate_confluence_score",
    "from entry_timing_engine import confirm_entry_candle",
    "from fii_dii_engine import analyze_fii_dii",
    "from market_status_engine import get_market_status",
    "from market_structure_engine import analyze_market_structure as analyze_candle_structure",
    "from multi_timeframe_engine import analyze_multi_timeframe",
]

for line in imports:
    if line not in text:
        anchor = "from price_action_engine import analyze_price_action"
        if anchor not in text:
            raise SystemExit("ERROR: Import anchor not found in main.py")
        text = text.replace(anchor, anchor + "\n" + line, 1)

block = '''
    # Current Indian market session status
    market_status = get_market_status()
    print("MARKET_STATUS:", market_status)

    # Analyze latest-candle market structure separately
    candle_structure = analyze_candle_structure(candles)
    print("CANDLE_MARKET_STRUCTURE:", candle_structure)

    # Fetch 15-minute candles for multi-timeframe comparison
    candles_15m = fetch_historical_data(
        kite=kite,
        instrument_token=token,
        from_date=from_date,
        to_date=to_date,
        interval="15minute",
    )

    print("15M_CANDLE_COUNT:", len(candles_15m))

    multi_timeframe = analyze_multi_timeframe(
        candles_15m=candles_15m,
        candles_5m=candles,
    )
    print("MULTI_TIMEFRAME_ANALYSIS:", multi_timeframe)

    # These engines need genuine inputs not yet produced by the current pipeline.
    print("FII_DII_SKIPPED: Real fii_net and dii_net data not available.")
    print("CONFLUENCE_SKIPPED: All 8 component scores are not yet available.")
    print("ENTRY_TIMING_SKIPPED: Direction and reference level are not yet confirmed.")
'''

anchor = '    print("MARKET_STRUCTURE_ANALYSIS:", market_analysis)'
if "MULTI_TIMEFRAME_ANALYSIS:" not in text:
    if anchor not in text:
        raise SystemExit("ERROR: Market structure output anchor not found.")
    text = text.replace(anchor, anchor + "\n" + block.rstrip(), 1)

path.write_text(text, encoding="utf-8")
print("UPDATED main.py")
