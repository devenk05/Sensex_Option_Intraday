"""Regression checks for JARVIS context mapping and review output.

These tests use synthetic data only: no Kite connection, network call, or broker action.
"""
import ast
import unittest
from pathlib import Path

from AgenticAI.agent_orchestrator import build_review


ROOT = Path(__file__).resolve().parents[1]


class AgenticAIPipelineVerificationTests(unittest.TestCase):
    def test_live_five_minute_path_dispatches_required_context(self):
        source = (ROOT / "Entry" / "main.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        target = next(
            node for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_evaluate_live_setup_on_completed_5m"
        )
        dispatch = [
            node for node in ast.walk(target)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "dispatch_agent_review"
        ]
        self.assertEqual(len(dispatch), 1, "Live 5m decision must dispatch exactly one advisory review call.")
        keyword_names = {kw.arg for kw in dispatch[0].keywords}
        self.assertTrue({
            "decision", "entry_score", "minimum_score", "market_analysis",
            "candle_structure", "multi_timeframe", "price_action",
            "cepe_comparison", "active_trade", "option_chain_available",
            "one_minute_confirmed", "risk_limit_inr",
        }.issubset(keyword_names))

    def test_synthetic_live_context_survives_review_with_expected_fields(self):
        context = {
            "decision": {
                "status": "TRADE_CANDIDATE",
                "candidate": {"symbol": "SENSEX_TEST_PE", "direction": "PE"},
            },
            "entry_score": 88,
            "minimum_score": 80,
            "market_analysis": {"trend": "DOWN"},
            "candle_structure": {"trend": "BEARISH"},
            "multi_timeframe": {"status": "OK", "direction": "BEARISH"},
            "price_action": {"signal": "BEARISH_CONTINUATION"},
            "cepe_comparison": {"status": "OK", "candidate_direction": "PE"},
            "active_trade": False,
            "option_chain_available": True,
            "one_minute_confirmed": True,
            "risk_limit_inr": 1000,
        }

        review = build_review(context)

        self.assertEqual(review["mode"], "ADVISORY_ONLY")
        self.assertEqual(review["market_intelligence"]["market_trend"], "DOWN")
        self.assertEqual(review["market_intelligence"]["multi_timeframe"]["direction"], "BEARISH")
        self.assertEqual(review["market_intelligence"]["candidate_direction"], "PE")
        self.assertEqual(review["decision_audit"]["decision_status"], "TRADE_CANDIDATE")
        self.assertEqual(review["decision_audit"]["entry_score"], 88.0)
        self.assertTrue(review["decision_audit"]["candidate_present"])
        self.assertEqual(review["risk_review"]["risk_limit_inr"], 1000.0)
        self.assertFalse(review["risk_review"]["broker_orders_enabled"])
        self.assertTrue(review["risk_review"]["recommendation_only"])

    def test_missing_score_remains_diagnostic_and_never_forces_entry(self):
        review = build_review({
            "decision": {"status": "WAIT", "candidate": None},
            "entry_score": None,
            "minimum_score": 80,
            "active_trade": False,
            "option_chain_available": False,
            "risk_limit_inr": 1000,
        })
        self.assertEqual(review["decision_audit"]["decision_status"], "WAIT")
        self.assertIn(
            "ENTRY_SCORE_MISSING_OR_NON_NUMERIC",
            review["decision_audit"]["diagnostic_flags"],
        )
        self.assertFalse(review["risk_review"]["broker_orders_enabled"])
        self.assertEqual(review["mode"], "ADVISORY_ONLY")


if __name__ == "__main__":
    unittest.main()
