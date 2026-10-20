"""Live same-contract IV snapshot sampling for the Sensex options runtime."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from liquidity_greeks_engine import analyze_liquidity_greeks
from vega_impact_engine import analyze_vega_impact

IST = ZoneInfo("Asia/Kolkata")


def _as_ist_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=IST)
    return parsed.astimezone(IST)


def update_live_vega_snapshots(
    selected_options: dict[str, dict[str, Any]],
    live_tick_state: dict[Any, dict[str, Any]],
    spot: Any,
    previous_snapshots: dict[str, dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
    max_tick_age_seconds: int = 120,
) -> dict[str, Any]:
    """Sample recent live CE/PE ticks and estimate same-contract Vega impact."""
    if max_tick_age_seconds <= 0:
        raise ValueError("max_tick_age_seconds must be positive.")
    current_time = now or datetime.now(IST)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=IST)
    else:
        current_time = current_time.astimezone(IST)

    previous = dict(previous_snapshots or {})
    updated = dict(previous)
    leg_results: dict[str, dict[str, Any]] = {}

    for option_type in ("CE", "PE"):
        option = selected_options.get(option_type)
        if not isinstance(option, dict) or not option:
            leg_results[option_type.lower()] = {
                "status": "UNAVAILABLE", "reason": "SELECTED_OPTION_UNAVAILABLE"
            }
            continue

        token = option.get("instrument_token")
        tick = live_tick_state.get(token)
        if not isinstance(tick, dict) and token is not None:
            tick = live_tick_state.get(str(token))
        if not isinstance(tick, dict):
            leg_results[option_type.lower()] = {
                "status": "UNAVAILABLE", "reason": "LIVE_TICK_UNAVAILABLE"
            }
            continue

        tick_time = _as_ist_datetime(tick.get("timestamp"))
        if tick_time is None:
            leg_results[option_type.lower()] = {
                "status": "UNAVAILABLE", "reason": "LIVE_TICK_TIMESTAMP_INVALID"
            }
            continue
        age_seconds = (current_time - tick_time).total_seconds()
        if age_seconds < 0 or age_seconds > max_tick_age_seconds:
            leg_results[option_type.lower()] = {
                "status": "UNAVAILABLE",
                "reason": "LIVE_TICK_STALE",
                "tick_age_seconds": round(age_seconds, 3),
            }
            continue

        greek_input = {**option, **tick, "spot": spot, "option_type": option_type}
        greek_result = analyze_liquidity_greeks(greek_input)
        if (
            greek_result.get("greeks_status") != "AVAILABLE"
            or greek_result.get("iv") is None
            or greek_result.get("vega") is None
        ):
            leg_results[option_type.lower()] = {
                "status": "UNAVAILABLE",
                "reason": greek_result.get("greeks_reason")
                or greek_result.get("reason")
                or "IV_OR_VEGA_UNAVAILABLE",
                "liquidity_status": greek_result.get("status"),
            }
            continue

        symbol = str(option.get("tradingsymbol") or "").strip().upper()
        if not symbol:
            leg_results[option_type.lower()] = {
                "status": "UNAVAILABLE", "reason": "TRADING_SYMBOL_MISSING"
            }
            continue

        current_snapshot = {
            "tradingsymbol": symbol,
            "expiry": option.get("expiry"),
            "strike": option.get("strike"),
            "option_type": option_type,
            "timestamp": tick_time.isoformat(),
            "iv": greek_result["iv"],
            "vega": greek_result["vega"],
            "last_price": tick.get("last_price"),
            "iv_price_source": greek_result.get("iv_price_source"),
        }
        impact = analyze_vega_impact(previous.get(symbol), current_snapshot)
        updated[symbol] = current_snapshot
        leg_results[option_type.lower()] = {
            "status": "OK",
            "greeks_status": "AVAILABLE",
            "liquidity_status": greek_result.get("status"),
            "iv": greek_result["iv"],
            "vega": greek_result["vega"],
            "iv_price_source": greek_result.get("iv_price_source"),
            "tick_age_seconds": round(age_seconds, 3),
            "impact": impact,
            "snapshot": current_snapshot,
        }

    statuses = [leg_results[key].get("status") for key in ("ce", "pe")]
    overall_status = (
        "OK" if statuses == ["OK", "OK"]
        else "PARTIAL" if "OK" in statuses
        else "NO_DATA"
    )
    return {
        "status": overall_status,
        "sampled_at": current_time.isoformat(),
        "source": "KITE_LIVE_TICK_PLUS_BLACK_SCHOLES_ESTIMATE",
        "directional_signal": False,
        "ce": leg_results["ce"],
        "pe": leg_results["pe"],
        "snapshots": updated,
    }
