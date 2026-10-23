import json
import tempfile
import unittest
from pathlib import Path

from AgenticAI import agent_config
from AgenticAI.agent_orchestrator import _persist_review, build_review
from report.dashboard import generate_dashboard


class AgenticAITests(unittest.TestCase):
    def test_review_is_advisory_and_does_not_emit_order(self):
        review = build_review({
            "decision": {"status": "WAIT", "candidate": None},
            "entry_score": 88,
            "minimum_score": 80,
            "market_analysis": {"trend": "DOWN"},
            "multi_timeframe": {"direction": "BEARISH"},
            "cepe_comparison": {"status": "OK", "candidate_direction": "PE"},
            "active_trade": False,
            "option_chain_available": True,
            "one_minute_confirmed": False,
            "risk_limit_inr": 1000,
        })
        self.assertEqual(review["mode"], "ADVISORY_ONLY")
        self.assertEqual(review["decision_audit"]["decision_status"], "WAIT")
        self.assertIn("SCORE_PASSES_BUT_DECISION_WAITS: inspect confirmation, veto, data freshness and decision stages",
                      review["decision_audit"]["diagnostic_flags"])
        self.assertFalse(review["risk_review"]["broker_orders_enabled"])
        self.assertTrue(review["risk_review"]["recommendation_only"])

    def test_top_level_candidate_contract_is_not_flagged_as_missing(self):
        review = build_review({
            "decision": {
                "status": "TRADE_CANDIDATE",
                "direction": "CE",
                "action": "BUY_CE",
                "entry_score": 88,
            },
            "entry_score": 88,
            "minimum_score": 80,
            "option_chain_available": True,
        })
        self.assertTrue(review["decision_audit"]["candidate_present"])
        self.assertNotIn(
            "TRADE_CANDIDATE_STATUS_WITHOUT_CANDIDATE_OBJECT",
            review["decision_audit"]["diagnostic_flags"],
        )

    def test_below_minimum_score_is_flagged(self):
        review = build_review({
            "decision": {"status": "WAIT"},
            "entry_score": 55,
            "minimum_score": 80,
            "active_trade": True,
            "risk_limit_inr": 1000,
        })
        self.assertIn("SCORE_BELOW_MINIMUM", review["decision_audit"]["diagnostic_flags"])
        self.assertIn("ACTIVE_TRADE_LOCK_MUST_PREVENT_NEW_ENTRY", review["risk_review"]["risk_flags"])

    def test_missing_data_is_not_treated_as_buy(self):
        review = build_review({})
        self.assertEqual(review["decision_audit"]["decision_status"], "UNKNOWN")
        self.assertIn("MISSING_SCORE", review["risk_review"]["risk_flags"])
        self.assertEqual(review["mode"], "ADVISORY_ONLY")

    def test_review_is_published_to_dashboard_snapshot(self):
        original_output = agent_config.OUTPUT_DIR
        original_dashboard_path = agent_config.DASHBOARD_REVIEW_PATH
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            agent_config.OUTPUT_DIR = root / "agentic_ai"
            agent_config.DASHBOARD_REVIEW_PATH = root / "dashboard" / "agentic_review.json"
            review = {
                "timestamp": "2026-10-21T10:00:00+05:30",
                "mode": "ADVISORY_ONLY",
                "decision_audit": {"decision_status": "WAIT"},
                "risk_review": {"broker_orders_enabled": False},
            }
            try:
                _persist_review(review)
                dashboard_review = json.loads(agent_config.DASHBOARD_REVIEW_PATH.read_text(encoding="utf-8"))
                latest_review = json.loads((agent_config.OUTPUT_DIR / "latest_review.json").read_text(encoding="utf-8"))
                self.assertEqual(dashboard_review, review)
                self.assertEqual(latest_review, review)
                self.assertTrue((agent_config.OUTPUT_DIR / "review_history.jsonl").exists())
            finally:
                agent_config.OUTPUT_DIR = original_output
                agent_config.DASHBOARD_REVIEW_PATH = original_dashboard_path

    def test_generated_dashboard_loads_agentic_panel_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "index.html"
            generate_dashboard(
                {"status": "Starting", "market_bias": "NEUTRAL", "decision": {"status": "WAIT"}},
                output_path=str(output_path),
            )
            html = output_path.read_text(encoding="utf-8")
            self.assertIn('<script src="agentic_panel.js"></script>', html)


if __name__ == "__main__":
    unittest.main()
