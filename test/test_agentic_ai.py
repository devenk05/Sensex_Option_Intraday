import json
from pathlib import Path

from AgenticAI import agent_orchestrator
from AgenticAI import agent_config


def test_build_review_is_advisory_and_contains_guardrail_sections(monkeypatch):
    monkeypatch.setattr(
        agent_orchestrator,
        "explain_review",
        lambda review: {"status": "DISABLED_FOR_TEST", "text": ""},
    )
    review = agent_orchestrator.build_review({
        "decision": {"status": "WAIT", "candidate": None},
        "entry_score": 88,
        "minimum_score": 80,
        "market_analysis": {"trend": "BULLISH"},
        "multi_timeframe": {"direction": "BEARISH", "status": "ALIGNED"},
        "cepe_comparison": {"candidate_direction": "PE"},
        "active_trade": False,
        "option_chain_available": True,
        "one_minute_confirmed": False,
        "risk_limit_inr": 1000,
    })

    assert review["mode"] == "ADVISORY_ONLY"
    assert review["decision_audit"]["decision_status"] == "WAIT"
    assert review["decision_audit"]["entry_score"] == 88.0
    assert "ONE_MINUTE_CONFIRMATION_FALSE_OR_MISSING" in review["decision_audit"]["diagnostic_flags"]
    assert review["risk_review"]["broker_orders_enabled"] is False
    assert review["risk_review"]["recommendation_only"] is True
    assert review["explanation"]["safety"]


def test_persist_review_writes_latest_dashboard_snapshot_and_history(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(agent_config, "OUTPUT_DIR", tmp_path / "data" / "agentic_ai")
    (tmp_path / "dashboard").mkdir()
    review = {
        "mode": "ADVISORY_ONLY",
        "timestamp": "2026-10-17T10:00:00+05:30",
        "decision_audit": {"decision_status": "WAIT"},
        "risk_review": {"broker_orders_enabled": False},
    }

    agent_orchestrator._persist_review(review)

    latest = agent_config.OUTPUT_DIR / "latest_review.json"
    dashboard_copy = tmp_path / "dashboard" / "latest_agentic_review.json"
    history = agent_config.OUTPUT_DIR / "review_history.jsonl"
    assert json.loads(latest.read_text(encoding="utf-8")) == review
    assert json.loads(dashboard_copy.read_text(encoding="utf-8")) == review
    assert json.loads(history.read_text(encoding="utf-8").splitlines()[-1]) == review
