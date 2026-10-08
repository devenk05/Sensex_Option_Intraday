from pathlib import Path

path = Path("main.py")
text = path.read_text(encoding="utf-8-sig")

imports = [
    "from veto_engine import check_trade_vetoes",
    "from volume_engine import analyze_volume",
    "from reversal_engine import detect_reversal",
    "from risk_manager import calculate_position_size",
    "from support_resistance_engine import calculate_support_resistance",
]

anchor = "from active_trade_manager import ActiveTradeManager"
if anchor not in text:
    raise SystemExit("ERROR: Existing import anchor not found.")

for line in imports:
    if line not in text:
        text = text.replace(anchor, anchor + "\n" + line, 1)

# Add live option volume and reversal analysis inside finalized-candle callback
callback_anchor = '        "RSI14:", indicators["rsi_14"],\n    )'
callback_block = '''

    # Analyze live option candle volume and reversal
    volume_analysis = analyze_volume(history)
    print("LIVE_OPTION_VOLUME_ANALYSIS:", volume_analysis)

    reversal_analysis = detect_reversal(history)
    print("LIVE_OPTION_REVERSAL_ANALYSIS:", reversal_analysis)
'''

if "LIVE_OPTION_VOLUME_ANALYSIS:" not in text:
    if callback_anchor not in text:
        raise SystemExit("ERROR: Indicator callback anchor not found.")
    text = text.replace(
        callback_anchor,
        callback_anchor + callback_block,
        1,
    )

# Add support/resistance analysis after existing market structure analysis
sr_anchor = '    print("CANDLE_MARKET_STRUCTURE:", candle_structure)'
sr_block = '''

    # Calculate Sensex support and resistance from historical candles
    support_resistance = calculate_support_resistance(candles)
    print("SUPPORT_RESISTANCE_ANALYSIS:", support_resistance)

    # These require valid trade-decision inputs that are not available yet.
    print("VETO_ENGINE_SKIPPED: Mandatory live confirmation checks are not ready.")
    print("RISK_MANAGER_SKIPPED: Requires option-premium entry and stop-loss values.")
'''

if "SUPPORT_RESISTANCE_ANALYSIS:" not in text:
    if sr_anchor not in text:
        raise SystemExit("ERROR: Market structure anchor not found.")
    text = text.replace(sr_anchor, sr_anchor + sr_block, 1)

path.write_text(text, encoding="utf-8")
print("UPDATED main.py")
