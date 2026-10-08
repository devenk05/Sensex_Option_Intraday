from pathlib import Path

p = Path(r".\Entry\trade_decision_flow.py")
s = p.read_text(encoding="utf-8")

marker = "def derive_market_bias("

helpers = '''def _num(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _option_volume(
    option_data: dict[str, Any] | None,
) -> float | None:
    data = option_data or {}
    return _num(data.get("volume"))


'''

if "def _num(" in s:
    print("SKIP: _num already exists")
elif marker not in s:
    raise SystemExit("ERROR: derive_market_bias marker not found")
else:
    s = s.replace(marker, helpers + marker, 1)
    p.write_text(s, encoding="utf-8")
    print("HELPERS ADDED")
