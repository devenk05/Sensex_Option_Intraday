
from typing import Any


def confirm_entry_candle(
    candles: list[dict[str, Any]],
    direction: str,
    reference_level: float,
) -> dict[str, Any]:
    """Check whether the latest candle closes beyond a reference level."""

    direction = direction.upper()

    if direction not in {"CE", "PE"}:
        raise ValueError("direction must be CE or PE.")

    if reference_level <= 0:
        raise ValueError("reference_level must be positive.")

    if not candles:
        return {
            "status": "NO_DATA",
            "confirmed": False,
        }

    latest = candles[-1]

    required = {"open", "high", "low", "close"}
    missing = required - latest.keys()

    if missing:
        raise ValueError(
            f"Latest candle is missing fields: {sorted(missing)}"
        )

    open_price = float(latest["open"])
    high = float(latest["high"])
    low = float(latest["low"])
    close = float(latest["close"])

    if high < low or not (
        low <= open_price <= high and low <= close <= high
    ):
        raise ValueError("Latest candle has invalid OHLC values.")

    if direction == "CE":
        confirmed = close > reference_level and close > open_price
    else:
        confirmed = close < reference_level and close < open_price

    return {
        "status": "OK",
        "confirmed": confirmed,
        "direction": direction,
        "close": close,
        "reference_level": reference_level,
    }