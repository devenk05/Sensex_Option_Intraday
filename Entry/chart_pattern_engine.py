
from typing import Any


def detect_candle_patterns(
    candles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Detect basic bullish/bearish candle patterns from OHLC data."""

    if not candles:
        return {
            "status": "NO_DATA",
            "patterns": [],
        }

    required = {"open", "high", "low", "close"}

    for index, candle in enumerate(candles):
        missing = required - candle.keys()
        if missing:
            raise ValueError(
                f"Candle {index} is missing fields: {sorted(missing)}"
            )

    latest = candles[-1]
    open_price = float(latest["open"])
    high = float(latest["high"])
    low = float(latest["low"])
    close = float(latest["close"])

    if high < low or not (low <= open_price <= high):
        raise ValueError("Latest candle has invalid OHLC values.")

    if not (low <= close <= high):
        raise ValueError("Latest candle has invalid OHLC values.")

    candle_range = high - low
    body = abs(close - open_price)
    patterns = []

    if candle_range == 0:
        return {
            "status": "OK",
            "patterns": ["DOJI"],
        }

    upper_wick = high - max(open_price, close)
    lower_wick = min(open_price, close) - low

    if body <= candle_range * 0.1:
        patterns.append("DOJI")

    if (
        body > 0
        and lower_wick >= body * 2
        and upper_wick <= body
    ):
        patterns.append(
            "BULLISH_HAMMER" if close >= open_price else "POSSIBLE_HAMMER"
        )

    if (
        body > 0
        and upper_wick >= body * 2
        and lower_wick <= body
    ):
        patterns.append(
            "BEARISH_SHOOTING_STAR"
            if close <= open_price
            else "POSSIBLE_SHOOTING_STAR"
        )

    return {
        "status": "OK",
        "patterns": patterns or ["NO_PATTERN"],
    }