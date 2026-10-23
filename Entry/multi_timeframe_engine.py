from typing import Any


def get_timeframe_direction(
    candles: list[dict[str, Any]],
) -> str:
    """Determine direction from the latest completed 5-minute candle."""

    if not candles:
        return "UNKNOWN"

    latest = candles[-1]
    required = {"open", "close"}
    missing = required - latest.keys()
    if missing:
        raise ValueError(f"Latest candle is missing fields: {sorted(missing)}")

    open_price = float(latest["open"])
    close_price = float(latest["close"])
    if close_price > open_price:
        return "BULLISH"
    if close_price < open_price:
        return "BEARISH"
    return "NEUTRAL"
