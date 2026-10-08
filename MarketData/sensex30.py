from __future__ import annotations

from typing import Any


SENSEX30_SYMBOLS = [
    "ADANIPORTS",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJFINSV",
    "BAJFINANCE",
    "BHARTIARTL",
    "ETERNAL",
    "HCLTECH",
    "HDFCBANK",
    "HINDUNILVR",
    "ICICIBANK",
    "INDUSINDBK",
    "INFY",
    "ITC",
    "KOTAKBANK",
    "LT",
    "M&M",
    "MARUTI",
    "NESTLEIND",
    "NTPC",
    "POWERGRID",
    "RELIANCE",
    "SBIN",
    "SUNPHARMA",
    "TMCV",
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",
    "ULTRACEMCO",
]


def get_sensex30_instruments(
    instruments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return BSE instruments matching the configured Sensex 30 symbols."""

    wanted = {symbol.upper() for symbol in SENSEX30_SYMBOLS}

    result = []

    for instrument in instruments:
        if str(instrument.get("exchange", "")).upper() != "BSE":
            continue

        symbol = str(instrument.get("tradingsymbol", "")).upper()

        if symbol in wanted:
            result.append(instrument)

    result.sort(
        key=lambda item: (
            SENSEX30_SYMBOLS.index(
                str(item.get("tradingsymbol", ""))
            )
            if str(item.get("tradingsymbol", "")) in SENSEX30_SYMBOLS
            else 999
        )
    )

    return result

