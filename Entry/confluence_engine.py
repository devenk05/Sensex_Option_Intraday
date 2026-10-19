from typing import Mapping


SCORING_WEIGHTS = {
    "market_structure": 15,
    "support_resistance": 15,
    "price_action": 20,
    "pivot_points": 10,
    "volume_analysis": 10,
    "fii_dii": 5,
    "atm_ce_pe_strength": 20,
    "liquidity_greeks": 5,
}

MAX_SCORE = 100


def calculate_confluence_score(
    component_scores: Mapping[str, float],
) -> dict[str, object]:
    """Calculate weighted evidence out of 100 without inflating missing data.

    Missing components earn no points and are reported separately. This is
    a partial evidence score, not a calibrated win probability.
    """

    unknown = set(component_scores) - set(SCORING_WEIGHTS)
    if unknown:
        raise ValueError(f"Unknown score components: {sorted(unknown)}")

    if not component_scores:
        return {
            "status": "NO_DATA",
            "score": None,
            "max_score": MAX_SCORE,
            "available_components": [],
            "unavailable_components": list(SCORING_WEIGHTS),
        }

    weighted_score = 0.0
    available_weight = 0

    for component, score_value in component_scores.items():
        score = float(score_value)

        if not 0 <= score <= 100:
            raise ValueError(
                f"{component} score must be between 0 and 100."
            )

        weight = SCORING_WEIGHTS[component]
        weighted_score += score * weight / 100
        available_weight += weight

    if available_weight <= 0:
        return {
            "status": "NO_DATA",
            "score": None,
            "max_score": MAX_SCORE,
            "available_components": [],
            "unavailable_components": list(SCORING_WEIGHTS),
        }

    # A single available component must not imply 100% confidence.
    # Preserve the full 100-point scale; missing evidence contributes no points.
    normalized_score = weighted_score
    unavailable = [
        component
        for component in SCORING_WEIGHTS
        if component not in component_scores
    ]

    return {
        "status": "OK",
        "score": round(normalized_score, 2),
        "coverage_percent": available_weight,
        "is_complete": available_weight == 100,
        "max_score": MAX_SCORE,
        "available_components": list(component_scores),
        "unavailable_components": unavailable,
        "available_weight": available_weight,
    }
