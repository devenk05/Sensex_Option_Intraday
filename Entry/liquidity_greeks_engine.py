from typing import Any


def analyze_liquidity_greeks(
    option: dict[str, Any],
    max_spread_percent: float = 2.0,
) -> dict[str, Any]:
    """Analyze real bid/ask liquidity and report Greeks only when supplied.

    Kite quote/depth data can provide bid/ask and quantities, but does not
    reliably provide option Greeks or implied volatility. Missing Greeks are
    reported as unavailable; they are never estimated or fabricated here.
    """

    if max_spread_percent <= 0:
        raise ValueError("max_spread_percent must be positive.")

    if not isinstance(option, dict):
        return {
            "status": "NO_DATA",
            "reason": "OPTION_DATA_UNAVAILABLE",
            "liquidity_passed": False,
            "liquidity_score": None,
            "greeks_status": "UNAVAILABLE",
        }

    def optional_float(key: str) -> float | None:
        value = option.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    bid = optional_float("bid")
    ask = optional_float("ask")

    if bid is None or ask is None or bid <= 0 or ask <= 0 or ask < bid:
        return {
            "status": "NO_DATA",
            "reason": "VALID_BID_ASK_UNAVAILABLE",
            "bid": bid,
            "ask": ask,
            "liquidity_passed": False,
            "liquidity_score": None,
            "greeks_status": "UNAVAILABLE",
            "greeks": {
                "delta": optional_float("delta"),
                "theta": optional_float("theta"),
                "iv": optional_float("iv"),
            },
        }

    midpoint = (bid + ask) / 2
    spread_percent = ((ask - bid) / midpoint) * 100 if midpoint > 0 else None
    liquid = spread_percent is not None and spread_percent <= max_spread_percent

    if spread_percent is None:
        liquidity_score = None
    elif spread_percent <= 0.5:
        liquidity_score = 100.0
    elif spread_percent <= 1.0:
        liquidity_score = 80.0
    elif spread_percent <= max_spread_percent:
        liquidity_score = 60.0
    else:
        liquidity_score = 25.0

    delta = optional_float("delta")
    theta = optional_float("theta")
    iv = optional_float("iv")
    greeks_available = all(value is not None for value in (delta, theta, iv))

    if delta is not None and not -1 <= delta <= 1:
        return {"status": "INVALID_DATA", "reason": "DELTA_OUT_OF_RANGE"}
    if iv is not None and iv < 0:
        return {"status": "INVALID_DATA", "reason": "IV_NEGATIVE"}

    return {
        "status": "OK",
        "bid": bid,
        "ask": ask,
        "midpoint": round(midpoint, 4),
        "spread_percent": round(spread_percent, 4) if spread_percent is not None else None,
        "max_spread_percent": max_spread_percent,
        "liquidity_passed": liquid,
        "liquidity_score": liquidity_score,
        "bid_quantity": optional_float("bid_quantity"),
        "ask_quantity": optional_float("ask_quantity"),
        "total_bid_quantity": optional_float("total_bid_quantity"),
        "total_ask_quantity": optional_float("total_ask_quantity"),
        "greeks_status": "AVAILABLE" if greeks_available else "NOT_PROVIDED_BY_QUOTE",
        "delta": delta,
        "theta": theta,
        "iv": iv,
    }
