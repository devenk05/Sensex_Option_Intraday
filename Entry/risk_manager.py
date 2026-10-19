from typing import Any


def calculate_stop_loss(
    entry_price: float,
    direction: str,
    recent_reversal_level: float,
) -> dict[str, Any]:
    """Use the latest structural reversal level without an arbitrary point cap.

    CE uses a reversal level below the entry; PE uses a reversal level above
    the entry (underlying-index direction). Position sizing must account for
    the returned structural risk before any recommendation is published.
    """
    entry = float(entry_price)
    reversal = float(recent_reversal_level)
    direction = str(direction or "").strip().upper()

    if entry <= 0:
        raise ValueError("entry_price must be positive.")

    if reversal <= 0:
        raise ValueError("recent_reversal_level must be positive.")

    if direction not in {"CE", "PE"}:
        raise ValueError("direction must be CE or PE.")

    if direction == "CE" and reversal >= entry:
        raise ValueError("For CE, reversal level must be below entry.")

    if direction == "PE" and reversal <= entry:
        raise ValueError("For PE, reversal level must be above entry.")

    stop_loss = reversal
    sl_points = abs(entry - stop_loss)

    return {
        "status": "OK",
        "direction": direction,
        "entry_price": round(entry, 2),
        "recent_reversal_level": round(reversal, 2),
        "stop_loss": round(stop_loss, 2),
        "sl_points": round(sl_points, 2),
        "structural_sl_used": True,
        "risk_exceeds_50_points": sl_points > 50.0,
        "max_sl_points": None,
    }
