
from typing import Any


def detect_reversal(
    candles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Detect a basic reversal using the last two candles."""

    if len(candles) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "signal": "UNKNOWN",
        }

    required = {"open", "high", "low", "close"}

    for index, candle in enumerate(candles[-2:]):
        missing = required - candle.keys()
        if missing:
            raise ValueError(
                f"Candle {index} is missing fields: {sorted(missing)}"
            )

    previous, latest = candles[-2], candles[-1]

    previous_open = float(previous["open"])
    previous_close = float(previous["close"])
    latest_open = float(latest["open"])
    latest_close = float(latest["close"])

    if (
        previous_close < previous_open
        and latest_close > latest_open
        and latest_close > previous_open
        and latest_open < previous_close
    ):
        signal = "BULLISH_ENGULFING"
    elif (
        previous_close > previous_open
        and latest_close < latest_open
        and latest_close < previous_open
        and latest_open > previous_close
    ):
        signal = "BEARISH_ENGULFING"
    else:
        signal = "NO_REVERSAL"

    return {
        "status": "OK",
        "signal": signal,
        "latest_close": latest_close,
    }