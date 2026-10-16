"""Independent guardrail review. It cannot place or close trades."""
from .agent_utils import as_dict


def run(context):
    active = bool(context.get("active_trade"))
    score = context.get("entry_score")
    try:
        score = float(score) if score is not None else None
    except (TypeError, ValueError):
        score = None
    try:
        minimum = float(context.get("minimum_score", 80))
    except (TypeError, ValueError):
        minimum = 80.0
    try:
        risk_limit = float(context.get("risk_limit_inr", 1000))
    except (TypeError, ValueError):
        risk_limit = 1000.0

    flags = []
    if active:
        flags.append("ACTIVE_TRADE_LOCK_MUST_PREVENT_NEW_ENTRY")
    if score is None:
        flags.append("MISSING_SCORE")
    elif score < minimum:
        flags.append("BELOW_MINIMUM_SCORE")
    if risk_limit <= 0:
        flags.append("INVALID_RISK_LIMIT_CONFIGURATION")
    return {
        "agent": "risk",
        "active_trade": active,
        "entry_score": score,
        "minimum_score": minimum,
        "risk_limit_inr": risk_limit,
        "risk_flags": flags or ["NO_BASIC_RISK_FLAG"],
        "broker_orders_enabled": False,
        "recommendation_only": True,
    }
