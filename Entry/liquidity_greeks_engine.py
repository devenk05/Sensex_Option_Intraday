
from typing import Any


def analyze_liquidity_greeks(
    option: dict[str, Any],
    max_spread_percent: float = 2.0,
) -> dict[str, Any]:
    """Validate option liquidity and supplied Greeks/IV values."""

    required = {
        "bid",
        "ask",
        "delta",
        "theta",
        "iv",
    }
    missing = required - option.keys()

    if missing:
        raise ValueError(
            f"Option data is missing fields: {sorted(missing)}"
        )

    bid = float(option["bid"])
    ask = float(option["ask"])
    delta = float(option["delta"])
    theta = float(option["theta"])
    iv = float(option["iv"])

    if bid < 0 or ask <= 0 or ask < bid:
        raise ValueError("Invalid bid/ask prices.")

    if not -1 <= delta <= 1:
        raise ValueError("Delta must be between -1 and 1.")

    if iv < 0:
        raise ValueError("IV cannot be negative.")

    midpoint = (bid + ask) / 2
    spread_percent = (
        ((ask - bid) / midpoint) * 100 if midpoint > 0 else None
    )

    liquid = (
        spread_percent is not None
        and spread_percent <= max_spread_percent
    )

    return {
        "status": "OK",
        "bid": bid,
        "ask": ask,
        "spread_percent": (
            round(spread_percent, 2)
            if spread_percent is not None
            else None
        ),
        "liquidity_passed": liquid,
        "delta": delta,
        "theta": theta,
        "iv": iv,
    }