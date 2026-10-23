"""Explain visible decision-state inconsistencies without overriding the decision."""
from .agent_utils import as_dict, first_present


def run(context):
    decision = as_dict(context.get("decision"))
    status = str(first_present(decision, "status", "decision", "action", default="UNKNOWN")).upper()
    # The decision-flow contract reports candidate direction/action at the
    # top level; it does not promise a nested "candidate" object.
    candidate = as_dict(decision.get("candidate"))
    candidate_present = bool(candidate) or (
        status == "TRADE_CANDIDATE"
        and str(first_present(decision, "direction", default="")).upper() in {"CE", "PE"}
        and str(first_present(decision, "action", default="")).upper() in {"BUY_CE", "BUY_PE"}
    )
    score = context.get("entry_score")
    try:
        score_value = float(score) if score is not None else None
    except (TypeError, ValueError):
        score_value = None
    minimum = context.get("minimum_score", 80)
    try:
        minimum_value = float(minimum)
    except (TypeError, ValueError):
        minimum_value = 80.0

    reasons = []
    if score_value is None:
        reasons.append("ENTRY_SCORE_MISSING_OR_NON_NUMERIC")
    elif score_value < minimum_value:
        reasons.append("SCORE_BELOW_MINIMUM")
    elif status in {"WAIT", "NO_TRADE", "SKIP", "REJECTED"}:
        reasons.append("SCORE_PASSES_BUT_DECISION_WAITS: inspect confirmation, veto, data freshness and decision stages")
    if not candidate_present and status == "TRADE_CANDIDATE":
        reasons.append("TRADE_CANDIDATE_STATUS_WITHOUT_CANDIDATE_OBJECT")
    if context.get("option_chain_available") is False:
        reasons.append("OPTION_CHAIN_UNAVAILABLE")
    if context.get("one_minute_confirmed") is False:
        reasons.append("ONE_MINUTE_CONFIRMATION_FALSE_OR_MISSING")

    return {
        "agent": "decision_audit",
        "decision_status": status,
        "entry_score": score_value,
        "minimum_score": minimum_value,
        "candidate_present": candidate_present,
        "diagnostic_flags": reasons or ["NO_BASIC_INCONSISTENCY_DETECTED"],
        "note": "Flags are diagnostic hints, not proof of a bug and never force an entry.",
    }
