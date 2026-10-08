from datetime import date
from typing import Any

from kiteconnect import KiteConnect


def fetch_sensex_options(
    kite: KiteConnect,
    strike_range: float = 200,
) -> dict[str, Any]:
    """Fetch nearest-expiry Sensex ATM and nearby CE/PE quotes.

    The result includes current premium, previous close, premium change,
    premium change %, OI and volume so the CE/PE relative-strength engine
    can compare both legs without recalculating market indicators.
    """

    sensex_quote = kite.ltp("BSE:SENSEX")
    spot = float(
        sensex_quote["BSE:SENSEX"]["last_price"]
    )

    instruments = kite.instruments("BFO")

    options = [
        item
        for item in instruments
        if "SENSEX" in str(
            item.get("name", "")
        ).upper()
        and item.get("instrument_type")
        in ("CE", "PE")
        and item.get("expiry")
        and item["expiry"] >= date.today()
        and float(
            item.get("strike", 0)
        ) > 0
    ]

    if not options:
        raise RuntimeError(
            "No current/future Sensex options found."
        )

    expiry = min(
        item["expiry"]
        for item in options
    )

    expiry_options = [
        item
        for item in options
        if item["expiry"] == expiry
    ]

    strikes = {
        float(item["strike"])
        for item in expiry_options
    }

    atm_strike = min(
        strikes,
        key=lambda strike: abs(
            strike - spot
        ),
    )

    selected = [
        item
        for item in expiry_options
        if abs(
            float(item["strike"])
            - atm_strike
        ) <= strike_range
    ]

    symbols = [
        f'BFO:{item["tradingsymbol"]}'
        for item in selected
    ]

    quotes = kite.quote(symbols)

    records: list[dict[str, Any]] = []

    for item in selected:
        symbol = (
            f'BFO:{item["tradingsymbol"]}'
        )

        quote = quotes.get(symbol)

        if not quote:
            continue

        if "last_price" not in quote:
            continue

        current = float(
            quote["last_price"]
        )

        ohlc = quote.get("ohlc") or {}
        previous_close = ohlc.get("close")

        if previous_close is not None:
            previous_close = float(
                previous_close
            )

        premium_change = None
        premium_change_percent = None

        if (
            previous_close is not None
            and previous_close != 0
        ):
            premium_change = (
                current
                - previous_close
            )

            premium_change_percent = (
                premium_change
                / abs(previous_close)
            ) * 100.0

        volume = float(
            quote.get(
                "volume",
                quote.get(
                    "volume_traded",
                    0,
                ),
            )
            or 0
        )

        records.append(
            {
                "tradingsymbol":
                    item["tradingsymbol"],

                "instrument_token":
                    item["instrument_token"],

                "expiry":
                    item["expiry"],

                "strike":
                    float(item["strike"]),

                "option_type":
                    item["instrument_type"],

                "last_price":
                    current,

                "previous_close":
                    previous_close,

                "premium_change":
                    premium_change,

                "premium_change_percent":
                    premium_change_percent,

                "oi":
                    float(
                        quote.get(
                            "oi",
                            0,
                        )
                    ),

                "volume":
                    volume,

                "lot_size":
                    item["lot_size"],
            }
        )

    return {
        "spot": spot,
        "expiry": expiry,
        "atm_strike": atm_strike,
        "options": records,
    }
