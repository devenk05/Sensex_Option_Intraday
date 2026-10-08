from pathlib import Path

p = Path(r".\Entry\trade_decision_flow.py")
s = p.read_text(encoding="utf-8-sig")

marker = """def derive_market_bias(
"""

helper = """def _premium_change_percent(option_data: dict[str, Any] | None) -> float | None:
    \"\"\"Return the existing option premium change percentage.

    option_data_pull.py provides this value as ``premium_change_percent``.
    \"\"\"
    data = option_data or {}

    value = data.get("premium_change_percent")

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


"""

if "_premium_change_percent(" in s:
    print("HELPER CALL EXISTS")

if "def _premium_change_percent(" in s:
    print("HELPER ALREADY EXISTS - NO CHANGES MADE")
    raise SystemExit(0)

if marker not in s:
    raise SystemExit("ERROR: Insert marker not found - NO CHANGES MADE")

backup = p.with_suffix(".py.before_premium_helper.bak")
backup.write_text(s, encoding="utf-8")

s = s.replace(marker, helper + marker, 1)
p.write_text(s, encoding="utf-8")

print("HELPER ADDED")
print("BACKUP:", backup)
