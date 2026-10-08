from typing import Any


MIN_ENTRY_SCORE = 80


def decide_trade(
    score: float,
    direction: str,
    veto_result: dict[str, Any],
    min_entry_score: float = MIN_ENTRY_SCORE,
) -> dict[str, Any]:
    """Return a trade candidate only when mandatory checks and score pass."""

    if not isinstance(veto_result, dict):
        raise TypeError("veto_result must be a dictionary.")

    if not isinstance(direction, str):
        raise TypeError("direction must be a string: CE or PE.")

    direction = direction.strip().upper()

    if direction not in {"CE", "PE"}:
        raise ValueError("direction must be CE or PE.")

    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise TypeError("score must be a number.")

    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100.")

    if not isinstance(min_entry_score, (int, float)) or isinstance(min_entry_score, bool):
        raise TypeError("min_entry_score must be a number.")

    if not 0 <= min_entry_score <= 100:
        raise ValueError("min_entry_score must be between 0 and 100.")

    if veto_result.get("approved") is not True:
        return {
            "status": "NO_TRADE",
            "reason": "MANDATORY_CHECK_FAILED",
            "score": score,
            "direction": None,
        }

    if score < min_entry_score:
        return {
            "status": "NO_TRADE",
            "reason": "SCORE_BELOW_THRESHOLD",
            "score": score,
            "direction": None,
        }

    return {
        "status": "TRADE_CANDIDATE",
        "reason": "ENTRY_CRITERIA_PASSED",
        "score": score,
        "direction": f"BUY_{direction}",
    }
