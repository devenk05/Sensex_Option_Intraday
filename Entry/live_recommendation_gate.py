"""Pure, testable safety gates for live trade recommendations."""
from datetime import datetime
import math
from zoneinfo import ZoneInfo

import config


def recommendation_time_gate_reason(now=None):
    """Return a rejection reason outside the allowed IST recommendation window.

    The start is inclusive (09:10 IST); the cutoff is exclusive (15:30 IST).
    Exit monitoring is intentionally not governed by this gate.
    """
    if now is None:
        now = datetime.now(ZoneInfo(config.TIMEZONE))
    elif now.tzinfo is None:
        # Tests/callers may supply a naive datetime; interpret it as IST.
        now = now.replace(tzinfo=ZoneInfo(config.TIMEZONE))
    else:
        now = now.astimezone(ZoneInfo(config.TIMEZONE))

    local_time = now.time().replace(tzinfo=None)
    if local_time < config.TRADING_START:
        return "BEFORE_TRADING_START"
    if local_time >= config.NO_NEW_RECOMMENDATIONS_AFTER:
        return "AFTER_RECOMMENDATION_CUTOFF"
    return None


def score_gate_reason(score, minimum=None):
    """Reject missing, non-numeric, or below-minimum recommendation scores."""
    if minimum is None:
        minimum = config.MIN_ENTRY_SCORE
    try:
        numeric_score = float(score)
        numeric_minimum = float(minimum)
    except (TypeError, ValueError, OverflowError):
        return "SCORE_BELOW_MINIMUM"
    if not math.isfinite(numeric_score) or not math.isfinite(numeric_minimum):
        return "SCORE_BELOW_MINIMUM"
    if numeric_score < numeric_minimum:
        return "SCORE_BELOW_MINIMUM"
    return None
