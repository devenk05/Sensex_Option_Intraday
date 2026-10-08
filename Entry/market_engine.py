
from typing import Any


def analyze_market_structure(
    candles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize recent candle structure using available OHLC data."""

    if not candles:
        return {
            "status": "NO_DATA",
            "trend": "UNKNOWN",
            "latest_close": None,
            "recent_high": None,
            "recent_low": None,
        }

    required = {"open", "high", "low", "close"}

    for index, candle in enumerate(candles):
        missing = required - candle.keys()
        if missing:
            raise ValueError(
                f"Candle {index} is missing fields: {sorted(missing)}"
            )

    latest_close = float(candles[-1]["close"])
    recent_high = max(float(candle["high"]) for candle in candles)
    recent_low = min(float(candle["low"]) for candle in candles)

    if len(candles) < 2:
        trend = "INSUFFICIENT_DATA"
    else:
        previous_close = float(candles[-2]["close"])

        if latest_close > previous_close:
            trend = "UP"
        elif latest_close < previous_close:
            trend = "DOWN"
        else:
            trend = "SIDEWAYS"

    return {
        "status": "OK",
        "trend": trend,
        "latest_close": latest_close,
        "recent_high": recent_high,
        "recent_low": recent_low,
    }