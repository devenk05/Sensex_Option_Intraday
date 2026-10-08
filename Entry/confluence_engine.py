
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
    """Calculate weighted score from component scores (0 to 100)."""

    unknown = set(component_scores) - set(SCORING_WEIGHTS)
    if unknown:
        raise ValueError(f"Unknown score components: {sorted(unknown)}")

    missing = set(SCORING_WEIGHTS) - set(component_scores)
    if missing:
        raise ValueError(f"Missing score components: {sorted(missing)}")

    weighted_score = 0.0

    for component, weight in SCORING_WEIGHTS.items():
        score = float(component_scores[component])

        if not 0 <= score <= 100:
            raise ValueError(
                f"{component} score must be between 0 and 100."
            )

        weighted_score += score * weight / 100

    return {
        "status": "OK",
        "score": round(weighted_score, 2),
        "max_score": MAX_SCORE,
    }