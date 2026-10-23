from math import isfinite
from typing import Any


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if isfinite(result) else None


def select_option(
    options: list[dict[str, Any]],
    target_strike: float,
    option_type: str,
    *,
    require_oi_increase: bool = False,
) -> dict[str, Any]:
    """Select the nearest usable contract; optionally require measured OI/volume build-up.

    The live recommendation path enables require_oi_increase so a contract is
    not selected from static OI/volume snapshots. Callers doing display-only
    ATM lookups may keep the backwards-compatible default.
    """
    option_type = str(option_type or "").upper()
    target = _number(target_strike)

    if option_type not in {"CE", "PE"}:
        raise ValueError("option_type must be CE or PE.")
    if target is None or target <= 0:
        raise ValueError("target_strike must be a finite positive number.")

    candidates = []
    for option in options:
        if not isinstance(option, dict) or str(option.get("option_type", "")).upper() != option_type:
            continue
        strike = _number(option.get("strike"))
        premium = _number(option.get("last_price"))
        if strike is None or strike <= 0 or premium is None or premium <= 0:
            continue
        if require_oi_increase:
            oi_change = _number(option.get("oi_change"))
            interval_volume = _number(option.get("interval_volume"))
            premium_change = _number(option.get("premium_change_5m"))
            if oi_change is None or oi_change <= 0:
                continue
            if interval_volume is None or interval_volume <= 0:
                continue
            if premium_change is None:
                continue
        candidates.append((option, strike))

    if not candidates:
        return {
            "status": "NO_MATCH",
            "option": None,
            "reason": "NO_FRESH_CONTRACT_WITH_REQUIRED_OI_VOLUME_DATA" if require_oi_increase else "NO_VALID_CONTRACT",
        }

    if require_oi_increase:
        selected, _ = min(
            candidates,
            key=lambda pair: (
                -(_number(pair[0].get("oi_change")) or 0.0),
                -(_number(pair[0].get("interval_volume")) or 0.0),
                abs(pair[1] - target),
            ),
        )
    else:
        selected, _ = min(candidates, key=lambda pair: abs(pair[1] - target))

    return {"status": "OK", "option": selected}
