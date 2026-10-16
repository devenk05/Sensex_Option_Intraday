import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from live_recommendation_gate import recommendation_time_gate_reason, score_gate_reason


IST = ZoneInfo("Asia/Kolkata")


class TestLiveRecommendationGate(unittest.TestCase):
    def test_before_start_is_blocked(self):
        self.assertEqual(
            recommendation_time_gate_reason(datetime(2026, 10, 16, 9, 9, 59, tzinfo=IST)),
            "BEFORE_TRADING_START",
        )

    def test_start_time_is_inclusive(self):
        self.assertIsNone(
            recommendation_time_gate_reason(datetime(2026, 10, 16, 9, 10, 0, tzinfo=IST))
        )

    def test_before_cutoff_is_allowed(self):
        self.assertIsNone(
            recommendation_time_gate_reason(datetime(2026, 10, 16, 15, 29, 59, tzinfo=IST))
        )

    def test_cutoff_time_is_blocked(self):
        self.assertEqual(
            recommendation_time_gate_reason(datetime(2026, 10, 16, 15, 30, 0, tzinfo=IST)),
            "AFTER_RECOMMENDATION_CUTOFF",
        )

    def test_timezone_is_normalized_to_ist(self):
        from datetime import timezone
        utc = datetime(2026, 10, 16, 10, 0, tzinfo=timezone.utc)  # 15:30 IST
        self.assertEqual(recommendation_time_gate_reason(utc), "AFTER_RECOMMENDATION_CUTOFF")

    def test_score_80_is_allowed(self):
        self.assertIsNone(score_gate_reason(80, 80))

    def test_score_above_80_is_allowed(self):
        self.assertIsNone(score_gate_reason(88, 80))

    def test_score_below_80_is_blocked(self):
        self.assertEqual(score_gate_reason(79.99, 80), "SCORE_BELOW_MINIMUM")

    def test_missing_or_invalid_score_is_blocked(self):
        for value in (None, "", "not-a-score"):
            with self.subTest(value=value):
                self.assertEqual(score_gate_reason(value, 80), "SCORE_BELOW_MINIMUM")


if __name__ == "__main__":
    unittest.main()
