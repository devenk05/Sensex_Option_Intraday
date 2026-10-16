"""Deterministic market summary agent. Does not calculate or change trade signals."""
from .agent_utils import as_dict, first_present


def run(context):
    market = as_dict(context.get("market_analysis"))
    structure = as_dict(context.get("candle_structure"))
    mtf = as_dict(context.get("multi_timeframe"))
    cepe = as_dict(context.get("cepe_comparison"))
    pa = as_dict(context.get("price_action"))
    return {
        "agent": "market_intelligence",
        "market_trend": first_present(market, "trend", "direction", "bias", default="UNKNOWN"),
        "candle_structure": first_present(structure, "trend", "structure", "direction", default="UNKNOWN"),
        "multi_timeframe": {
            "status": first_present(mtf, "status", default="UNKNOWN"),
            "direction": first_present(mtf, "direction", "trend", "bias", default="UNKNOWN"),
        },
        "cepe_status": first_present(cepe, "status", default="UNKNOWN"),
        "candidate_direction": first_present(cepe, "candidate_direction", "direction", default="UNKNOWN"),
        "price_action": first_present(pa, "signal", "bias", "trend", "status", default="UNKNOWN"),
        "summary": "Deterministic engines remain the source of truth; this summary is observational only.",
    }
