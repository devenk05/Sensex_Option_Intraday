import unittest

from AgenticAI.agent_orchestrator import build_review


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


if __name__ == "__main__":
    unittest.main()
