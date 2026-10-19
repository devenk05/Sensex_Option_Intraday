import unittest

from Entry.trade_decision_flow import run_locked_decision_flow


class LockedDecisionFlowTests(unittest.TestCase):
    def _inputs(self, one_minute_confirmed=False, score=88):
        return {
            "multi_timeframe": {
                "direction_15m": "BULLISH",
                "direction_5m": "BULLISH",
                "alignment": "ALIGNED",
            },
            "candle_structure": {"structure": "BULLISH"},
            "spot": 105.0,
            "pivot_analysis": {"pivot": 100.0},
            "price_action": {"signal": "BULLISH_CONTINUATION", "latest_close": 105.0},
            "volume_analysis": {"volume_ratio": 1.2},
            "oi_summary": {"call_oi": 100, "put_oi": 150},
            "ce": {
                "volume": 1000,
                "premium_change_percent": 1.2,
                "tradingsymbol": "SENSEXCE",
                "last_price": 150,
            },
            "pe": {
                "volume": 800,
                "premium_change_percent": -0.5,
                "tradingsymbol": "SENSEXPE",
                "last_price": 140,
            },
            "entry_score": score,
            "min_entry_score": 80,
            "one_minute_confirmed": one_minute_confirmed,
        }

    def test_score_88_does_not_bypass_missing_1m_confirmation(self):
        result = run_locked_decision_flow(**self._inputs(one_minute_confirmed=False, score=88))
        self.assertEqual(result["status"], "WAITING_FOR_1M_CONFIRMATION")
        self.assertIsNone(result["action"])
        stage = next(x for x in result["stages"] if x["stage"] == "ONE_MINUTE_ENTRY_CONFIRMATION")
        self.assertTrue(stage["required"])
        self.assertEqual(stage["status"], "WAIT")

    def test_aligned_1m_and_score_at_least_80_can_create_candidate(self):
        result = run_locked_decision_flow(**self._inputs(one_minute_confirmed=True, score=88))
        self.assertEqual(result["status"], "TRADE_CANDIDATE")
        self.assertEqual(result["action"], "BUY_CE")

    def test_score_below_80_is_rejected_even_with_1m_confirmation(self):
        result = run_locked_decision_flow(**self._inputs(one_minute_confirmed=True, score=79.99))
        self.assertEqual(result["status"], "NO_TRADE")
        self.assertEqual(result["reason"], "ENTRY_SCORE_BELOW_THRESHOLD")

    def test_invalid_or_out_of_range_score_is_rejected(self):
        for score in ("not-a-score", 101, -1):
            with self.subTest(score=score):
                result = run_locked_decision_flow(**self._inputs(one_minute_confirmed=True, score=score))
                self.assertEqual(result["status"], "NO_TRADE")


if __name__ == "__main__":
    unittest.main()
