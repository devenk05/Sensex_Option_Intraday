"""Fail-closed entry-quality checks for the live Sensex recommendation flow.

This module is pure Python: it never places orders and can be tested without Kite.
Index-point stop validation is deliberately separate from option-premium SL.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def finite_number(value: Any) -> float | None:
    """Convert a value to a finite float; reject missing, NaN and infinity."""
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def validate_index_stop(
    entry_index: Any,
    stop_index: Any,
    direction: str,
    max_points: float = 50.0,
) -> dict[str, Any]:
    """Validate an index-structure stop in SENSEX index points.

    BULLISH/CALL setups require the stop below entry; BEARISH/PUT setups
    require the stop above entry. This is not an option-premium stop.
    """
    entry = finite_number(entry_index)
    stop = finite_number(stop_index)
    limit = finite_number(max_points)
    side = str(direction or "").strip().upper()
    if entry is None or stop is None or limit is None or limit <= 0:
        return {"status": "WAIT", "reason": "INVALID_INDEX_ENTRY_OR_STOP"}
    if side in {"BULLISH", "CE", "CALL"}:
        distance = entry - stop
        valid_side = distance > 0
    elif side in {"BEARISH", "PE", "PUT"}:
        distance = stop - entry
        valid_side = distance > 0
    else:
        return {"status": "WAIT", "reason": "INVALID_MARKET_DIRECTION"}
    if not valid_side:
        return {"status": "WAIT", "reason": "INDEX_STOP_ON_WRONG_SIDE"}
    if distance > limit:
        return {
            "status": "WAIT",
            "reason": "INDEX_STOP_EXCEEDS_MAX_POINTS",
            "entry_index": entry,
            "index_sl": stop,
            "index_sl_points": round(distance, 2),
            "max_index_sl_points": limit,
        }
    return {
        "status": "PASS",
        "reason": "INDEX_STOP_WITHIN_LIMIT",
        "entry_index": entry,
        "index_sl": stop,
        "index_sl_points": round(distance, 2),
        "max_index_sl_points": limit,
    }


def timestamp_is_fresh(
    timestamp: Any,
    now: datetime | None = None,
    max_age_seconds: float = 120.0,
) -> bool:
    """Return true only when an explicit timestamp is parseable and fresh."""
    if timestamp is None:
        return False
    try:
        parsed = timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(str(timestamp))
    except (TypeError, ValueError):
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=IST)
    else:
        parsed = parsed.astimezone(IST)
    current = now or datetime.now(IST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=IST)
    else:
        current = current.astimezone(IST)
    age = (current - parsed).total_seconds()
    return 0 <= age <= max_age_seconds


def evaluate_directional_confluence(
    *,
    market_direction: str,
    price_action_signal: Any,
    volume_ratio: Any,
    ce_change_percent: Any,
    pe_change_percent: Any,
    reversal_signal: Any = None,
    pivot_signal: Any = None,
    chart_pattern_signal: Any = None,
    ce_oi_change: Any = None,
    pe_oi_change: Any = None,
) -> dict[str, Any]:
    """Check whether price action, volume, reversal/pivot/pattern and options
    support the same market direction. Missing/invalid core evidence => WAIT.
    OI is reported as context; rising OI alone does not imply direction.
    """
    direction = str(market_direction or "").strip().upper()
    if direction not in {"BULLISH", "BEARISH"}:
        return {"status": "WAIT", "reason": "MARKET_DIRECTION_UNCONFIRMED"}
    pa = str(price_action_signal or "").strip().upper()
    pa_aligned = pa.startswith(direction)
    ratio = finite_number(volume_ratio)
    ce_change = finite_number(ce_change_percent)
    pe_change = finite_number(pe_change_percent)
    if not pa or not pa_aligned:
        return {"status": "WAIT", "reason": "PRICE_ACTION_NOT_ALIGNED"}
    if ratio is None or ratio <= 1.0:
        return {"status": "WAIT", "reason": "FIVE_MINUTE_VOLUME_NOT_BUILDING"}
    if ce_change is None or pe_change is None:
        return {"status": "WAIT", "reason": "CE_PE_PREMIUM_CHANGE_UNAVAILABLE"}
    premium_spread = ce_change - pe_change
    premium_aligned = premium_spread > 0 if direction == "BULLISH" else premium_spread < 0
    if not premium_aligned:
        return {"status": "WAIT", "reason": "CE_PE_PREMIUM_DIRECTION_NOT_ALIGNED"}
    supporting = [
        str(value or "").strip().upper()
        for value in (reversal_signal, pivot_signal, chart_pattern_signal)
        if str(value or "").strip()
    ]
    aligned_support = any(
        value.startswith(direction)
        or (direction == "BULLISH" and value in {"ABOVE_PIVOT", "SUPPORT_HOLD", "BULLISH_REVERSAL"})
        or (direction == "BEARISH" and value in {"BELOW_PIVOT", "RESISTANCE_REJECTION", "BEARISH_REVERSAL"})
        for value in supporting
    )
    if not aligned_support:
        return {"status": "WAIT", "reason": "NO_REVERSAL_PIVOT_OR_PATTERN_SUPPORT"}
    return {
        "status": "PASS",
        "reason": "DIRECTIONAL_CONFLUENCE_CONFIRMED",
        "market_direction": direction,
        "option_side": "CE" if direction == "BULLISH" else "PE",
        "volume_ratio": ratio,
        "ce_change_percent": ce_change,
        "pe_change_percent": pe_change,
        "premium_spread_percent": round(premium_spread, 4),
        "price_action_signal": pa,
        "supporting_signals": supporting,
        "ce_oi_change": finite_number(ce_oi_change),
        "pe_oi_change": finite_number(pe_oi_change),
        "oi_note": "OI is contextual; OI increase alone is not directional confirmation.",
    }
