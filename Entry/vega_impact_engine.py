"""Vega-based option premium impact estimates.

This module deliberately estimates the premium effect of an IV change for the
same option contract. Vega is not a market-direction signal by itself.
"""
from __future__ import annotations

from datetime import date, datetime
from math import isfinite
from typing import Any


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if isfinite(result) else None


def _timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None

    # Treat naive timestamps as IST-compatible local timestamps consistently.
    # The caller should provide timestamps from one timezone/source.
    return parsed


def _contract_key(snapshot: dict[str, Any]) -> tuple[str, str, float, str] | None:
    symbol = str(snapshot.get("tradingsymbol") or "").strip().upper()
    expiry_value = snapshot.get("expiry")
    if isinstance(expiry_value, (date, datetime)):
        expiry = expiry_value.isoformat()[:10]
    else:
        expiry = str(expiry_value or "").strip()[:10]
    strike = _number(snapshot.get("strike"))
    option_type = str(snapshot.get("option_type") or "").strip().upper()

    if not symbol or not expiry or strike is None or strike <= 0:
        return None
    if option_type not in {"CE", "PE"}:
        return None
    return symbol, expiry, strike, option_type


def analyze_vega_impact(
    previous_snapshot: dict[str, Any] | None,
    current_snapshot: dict[str, Any] | None,
    max_snapshot_gap_seconds: int = 600,
) -> dict[str, Any]:
    """Estimate premium impact from IV change on the same contract.

    Required snapshot fields: tradingsymbol, expiry, strike, option_type,
    timestamp, iv (annualized percent), and vega (premium points per 1 IV
    percentage-point). No market-direction inference is made here.
    """
    unavailable = {
        "status": "UNAVAILABLE",
        "reason": None,
        "iv_change_points": None,
        "vega": None,
        "estimated_premium_impact_points": None,
        "impact_direction": "UNKNOWN",
        "method": "LINEAR_VEGA_APPROXIMATION",
    }
    if max_snapshot_gap_seconds <= 0:
        raise ValueError("max_snapshot_gap_seconds must be positive.")
    if not isinstance(previous_snapshot, dict) or not isinstance(current_snapshot, dict):
        return {**unavailable, "reason": "SNAPSHOT_MISSING"}

    previous_key = _contract_key(previous_snapshot)
    current_key = _contract_key(current_snapshot)
    if previous_key is None or current_key is None:
        return {**unavailable, "reason": "CONTRACT_IDENTITY_INCOMPLETE"}
    if previous_key != current_key:
        return {**unavailable, "reason": "CONTRACT_MISMATCH"}

    previous_time = _timestamp(previous_snapshot.get("timestamp"))
    current_time = _timestamp(current_snapshot.get("timestamp"))
    if previous_time is None or current_time is None:
        return {**unavailable, "reason": "TIMESTAMP_MISSING_OR_INVALID"}
    if previous_time.tzinfo != current_time.tzinfo:
        return {**unavailable, "reason": "TIMESTAMP_TIMEZONE_MISMATCH"}

    gap = (current_time - previous_time).total_seconds()
    if gap <= 0:
        return {**unavailable, "reason": "TIMESTAMP_NOT_INCREASING"}
    if gap > max_snapshot_gap_seconds:
        return {**unavailable, "reason": "SNAPSHOTS_TOO_FAR_APART"}

    previous_iv = _number(previous_snapshot.get("iv"))
    current_iv = _number(current_snapshot.get("iv"))
    current_vega = _number(current_snapshot.get("vega"))
    if (
        previous_iv is None or current_iv is None
        or previous_iv <= 0 or current_iv <= 0
        or current_vega is None or current_vega < 0
    ):
        return {**unavailable, "reason": "IV_OR_VEGA_UNAVAILABLE"}

    iv_change = current_iv - previous_iv
    impact = current_vega * iv_change
    if impact > 1e-9:
        direction = "PREMIUM_UP"
    elif impact < -1e-9:
        direction = "PREMIUM_DOWN"
    else:
        direction = "NEUTRAL"

    return {
        "status": "OK",
        "reason": None,
        "contract": {
            "tradingsymbol": current_key[0],
            "expiry": current_key[1],
            "strike": current_key[2],
            "option_type": current_key[3],
        },
        "snapshot_gap_seconds": round(gap, 3),
        "previous_iv": round(previous_iv, 4),
        "current_iv": round(current_iv, 4),
        "iv_change_points": round(iv_change, 4),
        "vega": round(current_vega, 6),
        "estimated_premium_impact_points": round(impact, 4),
        "impact_direction": direction,
        "method": "LINEAR_VEGA_APPROXIMATION",
        "warning": "Estimate only; ignores gamma, theta, spot movement, and changing IV/Greeks.",
    }
