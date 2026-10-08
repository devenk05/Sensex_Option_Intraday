
from typing import Any


def analyze_market_structure(
    candles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Classify basic market structure using the latest two candles."""

    if len(candles) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "structure": "UNKNOWN",
        }

    required = {"high", "low", "close"}

    for index, candle in enumerate(candles):
        missing = required - candle.keys()
        if missing:
            raise ValueError(
                f"Candle {index} is missing fields: {sorted(missing)}"
            )

    previous = candles[-2]
    latest = candles[-1]

    previous_high = float(previous["high"])
    previous_low = float(previous["low"])
    latest_high = float(latest["high"])
    latest_low = float(latest["low"])

    if latest_high > previous_high and latest_low > previous_low:
        structure = "BULLISH"
    elif latest_high < previous_high and latest_low < previous_low:
        structure = "BEARISH"
    else:
        structure = "MIXED"

    return {
        "status": "OK",
        "structure": structure,
        "latest_high": latest_high,
        "latest_low": latest_low,
        "latest_close": float(latest["close"]),
    }