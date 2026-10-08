
from typing import Any


def analyze_price_action(
    candles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze the latest candle's direction and range breakout."""

    if not candles:
        return {
            "status": "NO_DATA",
            "signal": "UNKNOWN",
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

    if high < low or not (
        low <= open_price <= high and low <= close <= high
    ):
        raise ValueError("Latest candle has invalid OHLC values.")

    if len(candles) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "signal": "UNKNOWN",
            "latest_close": close,
        }

    previous_high = float(candles[-2]["high"])
    previous_low = float(candles[-2]["low"])

    if close > open_price and close > previous_high:
        signal = "BULLISH_BREAKOUT"
    elif close < open_price and close < previous_low:
        signal = "BEARISH_BREAKDOWN"
    elif close > open_price:
        signal = "BULLISH"
    elif close < open_price:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"

    return {
        "status": "OK",
        "signal": signal,
        "latest_close": close,
        "previous_high": previous_high,
        "previous_low": previous_low,
    }