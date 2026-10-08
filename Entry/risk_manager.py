from typing import Any


MAX_SL_POINTS = 50.0


def calculate_stop_loss(
    entry_price: float,
    direction: str,
    recent_reversal_level: float,
) -> dict[str, Any]:
    """Calculate Sensex index-point SL using the nearer of reversal and 50 points."""

    entry = float(entry_price)
    reversal = float(recent_reversal_level)
    direction = direction.upper()

    if entry <= 0:
        raise ValueError("entry_price must be positive.")

    if reversal <= 0:
        raise ValueError("recent_reversal_level must be positive.")

    if direction not in {"CE", "PE"}:
        raise ValueError("direction must be CE or PE.")

    if direction == "CE":
        if reversal >= entry:
            raise ValueError("For CE, reversal level must be below entry.")

        max_sl_level = entry - MAX_SL_POINTS
        stop_loss = max(reversal, max_sl_level)

    else:
        if reversal <= entry:
            raise ValueError("For PE, reversal level must be above entry.")

        max_sl_level = entry + MAX_SL_POINTS
        stop_loss = min(reversal, max_sl_level)

    return {
        "status": "OK",
        "direction": direction,
        "entry_price": round(entry, 2),
        "recent_reversal_level": round(reversal, 2),
        "stop_loss": round(stop_loss, 2),
        "sl_points": round(abs(entry - stop_loss), 2),
        "max_sl_points": MAX_SL_POINTS,
    }
