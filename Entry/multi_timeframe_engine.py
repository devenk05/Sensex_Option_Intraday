
from typing import Any


def get_timeframe_direction(
    candles: list[dict[str, Any]],
) -> str:
    """Determine direction from the latest candle's close vs open."""

    if not candles:
        return "UNKNOWN"

    latest = candles[-1]

    required = {"open", "close"}
    missing = required - latest.keys()

    if missing:
        raise ValueError(
            f"Latest candle is missing fields: {sorted(missing)}"
        )

    open_price = float(latest["open"])
    close_price = float(latest["close"])

    if close_price > open_price:
        return "BULLISH"
    if close_price < open_price:
        return "BEARISH"

    return "NEUTRAL"


def analyze_multi_timeframe(
    candles_15m: list[dict[str, Any]],
    candles_5m: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare 15-minute and 5-minute candle directions."""

    direction_15m = get_timeframe_direction(candles_15m)
    direction_5m = get_timeframe_direction(candles_5m)

    if "UNKNOWN" in {direction_15m, direction_5m}:
        alignment = "INSUFFICIENT_DATA"
    elif direction_15m == direction_5m:
        alignment = (
            "ALIGNED"
            if direction_15m != "NEUTRAL"
            else "NEUTRAL"
        )
    else:
        alignment = "NOT_ALIGNED"

    return {
        "status": "OK",
        "direction_15m": direction_15m,
        "direction_5m": direction_5m,
        "alignment": alignment,
    }