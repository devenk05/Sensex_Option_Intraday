from __future__ import annotations

import math
import os
from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")
DEFAULT_RISK_FREE_RATE = float(os.getenv("SENSEX_RISK_FREE_RATE", "0.10"))
DEFAULT_DIVIDEND_YIELD = float(os.getenv("SENSEX_DIVIDEND_YIELD", "0.0"))


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def _expiry_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        expiry_date = value.date()
    elif isinstance(value, date):
        expiry_date = value
    elif isinstance(value, str):
        try:
            expiry_date = date.fromisoformat(value[:10])
        except ValueError:
            return None
    else:
        return None

    # Indian index options stop trading at 15:30 IST on expiry day.
    return datetime.combine(expiry_date, time(15, 30), tzinfo=IST)


def _years_to_expiry(value: Any, now: datetime | None = None) -> float | None:
    expiry = _expiry_datetime(value)
    if expiry is None:
        return None
    current = now or datetime.now(IST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=IST)
    else:
        current = current.astimezone(IST)
    seconds = (expiry - current).total_seconds()
    if seconds <= 0:
        return None
    return seconds / (365.0 * 24.0 * 60.0 * 60.0)


def _black_scholes_price(
    spot: float,
    strike: float,
    years: float,
    rate: float,
    volatility: float,
    option_type: str,
    dividend_yield: float,
) -> float:
    if years <= 0:
        return max(spot - strike, 0.0) if option_type == "CE" else max(strike - spot, 0.0)
    if volatility <= 0:
        discounted_spot = spot * math.exp(-dividend_yield * years)
        discounted_strike = strike * math.exp(-rate * years)
        return max(discounted_spot - discounted_strike, 0.0) if option_type == "CE" else max(discounted_strike - discounted_spot, 0.0)

    root_t = math.sqrt(years)
    d1 = (
        math.log(spot / strike)
        + (rate - dividend_yield + 0.5 * volatility * volatility) * years
    ) / (volatility * root_t)
    d2 = d1 - volatility * root_t
    if option_type == "CE":
        return (
            spot * math.exp(-dividend_yield * years) * _normal_cdf(d1)
            - strike * math.exp(-rate * years) * _normal_cdf(d2)
        )
    return (
        strike * math.exp(-rate * years) * _normal_cdf(-d2)
        - spot * math.exp(-dividend_yield * years) * _normal_cdf(-d1)
    )


def _implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    years: float,
    rate: float,
    option_type: str,
    dividend_yield: float,
) -> float | None:
    if market_price <= 0 or years <= 0:
        return None

    low, high = 1e-4, 5.0
    low_price = _black_scholes_price(
        spot, strike, years, rate, low, option_type, dividend_yield
    )
    high_price = _black_scholes_price(
        spot, strike, years, rate, high, option_type, dividend_yield
    )
    if market_price < low_price - 0.05 or market_price > high_price + 0.05:
        return None

    for _ in range(100):
        mid = (low + high) / 2.0
        model_price = _black_scholes_price(
            spot, strike, years, rate, mid, option_type, dividend_yield
        )
        if abs(model_price - market_price) < 1e-5:
            return mid
        if model_price < market_price:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def _calculate_greeks(
    spot: float,
    strike: float,
    years: float,
    rate: float,
    volatility: float,
    option_type: str,
    dividend_yield: float,
) -> dict[str, float] | None:
    if min(spot, strike, years, volatility) <= 0:
        return None

    root_t = math.sqrt(years)
    d1 = (
        math.log(spot / strike)
        + (rate - dividend_yield + 0.5 * volatility * volatility) * years
    ) / (volatility * root_t)
    d2 = d1 - volatility * root_t
    discount_q = math.exp(-dividend_yield * years)
    discount_r = math.exp(-rate * years)
    pdf = _normal_pdf(d1)

    if option_type == "CE":
        delta = discount_q * _normal_cdf(d1)
        theta_year = (
            -spot * discount_q * pdf * volatility / (2.0 * root_t)
            - rate * strike * discount_r * _normal_cdf(d2)
            + dividend_yield * spot * discount_q * _normal_cdf(d1)
        )
    else:
        delta = discount_q * (_normal_cdf(d1) - 1.0)
        theta_year = (
            -spot * discount_q * pdf * volatility / (2.0 * root_t)
            + rate * strike * discount_r * _normal_cdf(-d2)
            - dividend_yield * spot * discount_q * _normal_cdf(-d1)
        )

    return {
        "delta": delta,
        "theta_per_day": theta_year / 365.0,
        "gamma": discount_q * pdf / (spot * volatility * root_t),
        "vega_per_1pct_iv": spot * discount_q * pdf * root_t / 100.0,
    }


def analyze_liquidity_greeks(
    option: dict[str, Any],
    max_spread_percent: float = 2.0,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    dividend_yield: float = DEFAULT_DIVIDEND_YIELD,
) -> dict[str, Any]:
    """Analyze real bid/ask liquidity and estimate Greeks from market prices.

    Greeks and IV are Black-Scholes estimates, not fields supplied by Kite.
    IV is solved from the bid/ask midpoint (or LTP fallback), with expiry
    timestamp 15:30 Asia/Kolkata, configurable annual risk-free rate, and
    configurable dividend-yield assumption. Missing inputs stay unavailable.
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
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError):
            return None

    bid = optional_float("bid")
    ask = optional_float("ask")
    last_price = optional_float("last_price")
    spot = optional_float("spot")
    strike = optional_float("strike")
    option_type = str(option.get("option_type") or "").upper()
    years = _years_to_expiry(option.get("expiry"))

    if bid is None or ask is None or bid <= 0 or ask <= 0 or ask < bid:
        return {
            "status": "NO_DATA",
            "reason": "VALID_BID_ASK_UNAVAILABLE",
            "bid": bid,
            "ask": ask,
            "liquidity_passed": False,
            "liquidity_score": None,
            "greeks_status": "UNAVAILABLE",
        }

    midpoint = (bid + ask) / 2.0
    spread_percent = ((ask - bid) / midpoint) * 100.0 if midpoint > 0 else None
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

    market_price = midpoint if midpoint > 0 else last_price
    iv = None
    greeks = None
    greeks_reason = "MODEL_INPUTS_UNAVAILABLE"

    if (
        market_price is not None and market_price > 0
        and spot is not None and spot > 0
        and strike is not None and strike > 0
        and option_type in {"CE", "PE"}
        and years is not None
    ):
        iv = _implied_volatility(
            market_price, spot, strike, years,
            risk_free_rate, option_type, dividend_yield,
        )
        if iv is not None:
            greeks = _calculate_greeks(
                spot, strike, years, risk_free_rate, iv,
                option_type, dividend_yield,
            )
            greeks_reason = "OK" if greeks else "GREEKS_CALCULATION_FAILED"
        else:
            greeks_reason = "IV_SOLVER_DID_NOT_CONVERGE_OR_PRICE_OUT_OF_BOUNDS"
    elif years is None:
        greeks_reason = "EXPIRY_MISSING_OR_EXPIRED"

    greeks_available = iv is not None and greeks is not None
    return {
        "status": "OK",
        "bid": bid,
        "ask": ask,
        "last_price": last_price,
        "midpoint": round(midpoint, 4),
        "spread_percent": round(spread_percent, 4) if spread_percent is not None else None,
        "max_spread_percent": max_spread_percent,
        "liquidity_passed": liquid,
        "liquidity_score": liquidity_score,
        "bid_quantity": optional_float("bid_quantity"),
        "ask_quantity": optional_float("ask_quantity"),
        "total_bid_quantity": optional_float("total_bid_quantity"),
        "total_ask_quantity": optional_float("total_ask_quantity"),
        "greeks_status": "AVAILABLE" if greeks_available else "UNAVAILABLE",
        "greeks_method": "BLACK_SCHOLES_ESTIMATE" if greeks_available else None,
        "iv": round(iv * 100.0, 4) if iv is not None else None,
        "iv_unit": "ANNUAL_PERCENT",
        "delta": round(greeks["delta"], 6) if greeks else None,
        "theta": round(greeks["theta_per_day"], 6) if greeks else None,
        "gamma": round(greeks["gamma"], 8) if greeks else None,
        "vega": round(greeks["vega_per_1pct_iv"], 6) if greeks else None,
        "theta_unit": "PREMIUM_POINTS_PER_CALENDAR_DAY",
        "risk_free_rate_percent": round(risk_free_rate * 100.0, 4),
        "dividend_yield_percent": round(dividend_yield * 100.0, 4),
        "years_to_expiry": round(years, 8) if years is not None else None,
        "greeks_reason": greeks_reason,
        "iv_price_source": "BID_ASK_MIDPOINT" if midpoint > 0 else "LTP",
        "model_assumptions": "EUROPEAN_BLACK_SCHOLES_SPOT_BASED",
    }
