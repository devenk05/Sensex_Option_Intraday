
from typing import Any


def calculate_support_resistance(
    candles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate basic support and resistance from candle highs/lows."""

    if not candles:
        return {
            "status": "NO_DATA",
            "support": None,
            "resistance": None,
        }

    required = {"high", "low"}

    for index, candle in enumerate(candles):
        missing = required - candle.keys()
        if missing:
            raise ValueError(
                f"Candle {index} is missing fields: {sorted(missing)}"
            )

    support = min(float(candle["low"]) for candle in candles)
    resistance = max(float(candle["high"]) for candle in candles)

    return {
        "status": "OK",
        "support": support,
        "resistance": resistance,
    }