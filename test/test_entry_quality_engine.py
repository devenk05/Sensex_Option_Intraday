import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from entry_quality_engine import (
    evaluate_directional_confluence,
    finite_number,
    timestamp_is_fresh,
    validate_index_stop,
)


class TestEntryQualityEngine(unittest.TestCase):
    def test_non_finite_values_are_rejected(self):
        for value in (None, "x", float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                self.assertIsNone(finite_number(value))

    def test_bullish_index_stop_within_50_points(self):
        result = validate_index_stop(72000, 71960, "BULLISH")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["index_sl_points"], 40)

    def test_bearish_index_stop_within_50_points(self):
        result = validate_index_stop(72000, 72050, "BEARISH")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["index_sl_points"], 50)

    def test_index_stop_over_50_points_is_blocked(self):
        result = validate_index_stop(72000, 71949, "BULLISH")
        self.assertEqual(result["status"], "WAIT")
        self.assertEqual(result["reason"], "INDEX_STOP_EXCEEDS_MAX_POINTS")

    def test_stop_must_be_on_correct_side(self):
        self.assertEqual(validate_index_stop(72000, 72010, "BULLISH")["status"], "WAIT")
        self.assertEqual(validate_index_stop(72000, 71990, "BEARISH")["status"], "WAIT")

    def test_missing_or_nonfinite_stop_is_blocked(self):
        for value in (None, float("nan"), float("inf")):
            self.assertEqual(validate_index_stop(72000, value, "BULLISH")["status"], "WAIT")

    def test_fresh_timestamp_requires_timezone_safe_age(self):
        now = datetime(2026, 10, 23, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        self.assertTrue(timestamp_is_fresh("2026-10-23T09:59:00+05:30", now, 120))
        self.assertFalse(timestamp_is_fresh("2026-10-23T09:55:00+05:30", now, 120))
        self.assertFalse(timestamp_is_fresh(None, now, 120))

    def test_aligned_confluence_passes(self):
        result = evaluate_directional_confluence(
            market_direction="BULLISH",
            price_action_signal="BULLISH_BREAKOUT",
            volume_ratio=1.5,
            ce_change_percent=2.0,
            pe_change_percent=-1.0,
            reversal_signal="BULLISH_ENGULFING",
            pivot_signal="ABOVE_PIVOT",
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["option_side"], "CE")

    def test_both_option_premiums_rising_is_not_directional_confirmation(self):
        result = evaluate_directional_confluence(
            market_direction="BULLISH",
            price_action_signal="BULLISH_BREAKOUT",
            volume_ratio=1.5,
            ce_change_percent=2.0,
            pe_change_percent=0.5,
            reversal_signal="BULLISH_ENGULFING",
        )
        self.assertEqual(result["status"], "WAIT")
        self.assertEqual(
            result["reason"],
            "CE_PE_PREMIUMS_NOT_MOVING_IN_OPPOSITE_CONFIRMED_DIRECTIONS",
        )

    def test_missing_or_conflicting_evidence_waits(self):
        base = dict(
            market_direction="BEARISH",
            price_action_signal="BEARISH_BREAKDOWN",
            volume_ratio=1.5,
            ce_change_percent=2.0,
            pe_change_percent=-1.0,
            reversal_signal="BEARISH_ENGULFING",
        )
        result = evaluate_directional_confluence(**base)
        self.assertEqual(result["status"], "WAIT")
        self.assertEqual(result["reason"], "CE_PE_PREMIUMS_NOT_MOVING_IN_OPPOSITE_CONFIRMED_DIRECTIONS")
        base["ce_change_percent"] = None
        self.assertEqual(evaluate_directional_confluence(**base)["status"], "WAIT")


if __name__ == "__main__":
    unittest.main()
