"""Pure direction-matching rules for the live 1-minute entry confirmation."""

VALID_DIRECTIONS = {"BULLISH", "BEARISH"}


def evaluate_entry_confirmation(direction_15m, direction_5m, signal):
    """Confirm only when 15m, 5m, and the directional 1m signal agree.

    This function confirms direction only. It does not authorize order placement;
    score, risk, active-trade, and other gates remain separate.
    """
    direction_15m = str(direction_15m or "").strip().upper()
    direction_5m = str(direction_5m or "").strip().upper()
    signal = str(signal or "UNKNOWN").strip().upper()

    if signal.startswith("BULLISH"):
        raw_direction = "BULLISH"
    elif signal.startswith("BEARISH"):
        raw_direction = "BEARISH"
    else:
        raw_direction = "WAIT"

    mtf_aligned = (
        direction_15m in VALID_DIRECTIONS
        and direction_15m == direction_5m
    )
    entry_confirmed = mtf_aligned and raw_direction == direction_15m

    return {
        "signal": signal,
        "raw_direction": raw_direction,
        "mtf_aligned": mtf_aligned,
        "entry_confirmed": entry_confirmed,
        "direction": raw_direction if entry_confirmed else "WAIT",
        "reason": (
            "1M_DIRECTION_ALIGNED_WITH_15M_5M"
            if entry_confirmed
            else "WAITING_FOR_DIRECTIONAL_1M_CANDLE_AND_MTF_ALIGNMENT"
        ),
    }
