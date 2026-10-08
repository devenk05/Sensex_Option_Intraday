from pathlib import Path

path = Path("main.py")
text = path.read_text(encoding="utf-8-sig")

# Add imports only if missing
imports = [
    ("from active_trade_manager import ActiveTradeManager",
     "from active_trade_manager import ActiveTradeManager"),
    ("from chart_pattern_engine import detect_candle_patterns",
     "from chart_pattern_engine import detect_candle_patterns"),
]

for marker, import_line in imports:
    if import_line not in text:
        anchor = "from price_action_engine import analyze_price_action"
        if anchor in text:
            text = text.replace(anchor, anchor + "\n" + import_line, 1)
        else:
            text = import_line + "\n" + text

# Add manager instance after CANDLE_HISTORY declaration
manager_line = "ACTIVE_TRADE_MANAGER = ActiveTradeManager()"
if manager_line not in text:
    anchor = "CANDLE_HISTORY = {}"
    if anchor not in text:
        raise SystemExit("ERROR: CANDLE_HISTORY declaration not found.")
    text = text.replace(anchor, anchor + "\n" + manager_line, 1)

# Add chart pattern analysis after price action analysis
pattern_block = '''    # Analyze candle patterns from historical Sensex candles
    chart_patterns = detect_candle_patterns(candles)
    print("CHART_PATTERN_ANALYSIS:", chart_patterns)

    # Report current active-trade manager state
    print("ACTIVE_TRADE_EXISTS:", ACTIVE_TRADE_MANAGER.has_active_trade())
    print("ACTIVE_TRADE:", ACTIVE_TRADE_MANAGER.get_active_trade())
'''

anchor = '    print("PRICE_ACTION_ANALYSIS:", price_action)'
if "CHART_PATTERN_ANALYSIS:" not in text:
    if anchor not in text:
        raise SystemExit("ERROR: Price action output anchor not found.")
    text = text.replace(anchor, anchor + "\n\n" + pattern_block.rstrip(), 1)

path.write_text(text, encoding="utf-8")
print("UPDATED main.py")
