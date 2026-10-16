"""Readable explanation generated from agent findings; no trade authority."""
def run(market, audit, risk):
    market = market if isinstance(market, dict) else {}
    audit = audit if isinstance(audit, dict) else {}
    risk = risk if isinstance(risk, dict) else {}
    flags = list(audit.get("diagnostic_flags") or []) + list(risk.get("risk_flags") or [])
    return {
        "agent": "explanation",
        "headline": "JARVIS diagnostic review complete",
        "market_summary": (
            f"Trend={market.get('market_trend', 'UNKNOWN')}; "
            f"MTF={market.get('multi_timeframe', {}).get('direction', 'UNKNOWN')}; "
            f"CE/PE={market.get('candidate_direction', 'UNKNOWN')}"
        ),
        "decision_summary": (
            f"Decision={audit.get('decision_status', 'UNKNOWN')}; "
            f"score={audit.get('entry_score', 'UNKNOWN')}/{audit.get('minimum_score', 80)}"
        ),
        "flags": flags,
        "safety": "Existing deterministic decision and risk rules remain authoritative. No order was placed.",
    }
