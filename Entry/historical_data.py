
from datetime import datetime
from typing import Any

from kiteconnect import KiteConnect


def fetch_historical_data(
    kite: KiteConnect,
    instrument_token: int,
    from_date: datetime,
    to_date: datetime,
    interval: str = "5minute",
) -> list[dict[str, Any]]:
    """Fetch historical candle data from Zerodha Kite."""

    if instrument_token <= 0:
        raise ValueError("instrument_token must be a positive integer.")

    if from_date >= to_date:
        raise ValueError("from_date must be earlier than to_date.")

    return kite.historical_data(
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
    )