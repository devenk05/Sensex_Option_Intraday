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
    """Calculate a normalized weighted score from available components.

    Components whose data is genuinely unavailable are omitted rather than
    being assigned a fabricated score. The returned score is normalized to
    0-100 using only the available component weights.
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

    normalized_score = weighted_score * 100 / available_weight
    unavailable = [
        component
        for component in SCORING_WEIGHTS
        if component not in component_scores
    ]

    return {
        "status": "OK",
        "score": round(normalized_score, 2),
        "max_score": MAX_SCORE,
        "available_components": list(component_scores),
        "unavailable_components": unavailable,
        "available_weight": available_weight,
    }
