import unittest

from tools.timeframe_replay import run_replay, signal_direction


def row(ts, d15, d5, pa, pe_open=100, pe_high=130, pe_low=95, pe_close=125,
        ce_open=100, ce_high=110, ce_low=90, ce_close=95):
    return {
        "timestamp": ts, "direction_15m": d15, "direction_5m": d5,
        "price_action_signal": pa, "score": "88", "min_score": "80",
        "mandatory_checks_pass": "true",
        "ce_open": str(ce_open), "ce_high": str(ce_high), "ce_low": str(ce_low),
        "ce_close": str(ce_close), "ce_sl": "80", "ce_target": "120",
        "pe_open": str(pe_open), "pe_high": str(pe_high), "pe_low": str(pe_low),
        "pe_close": str(pe_close), "pe_sl": "80", "pe_target": "120",
    }


class TimeframeReplayTests(unittest.TestCase):
    def test_strict_timeframe_gate_rejects_conflict_but_5m_only_accepts(self):
        sample = row("09:30", "BULLISH", "BEARISH", "BEARISH_BREAKDOWN")
        self.assertIsNone(signal_direction(sample, "15m+5m"))
        self.assertEqual(signal_direction(sample, "5m-only"), "PE")

    def test_same_direction_is_eligible_for_both(self):
        sample = row("09:30", "BEARISH", "BEARISH", "BEARISH_BREAKDOWN")
        self.assertEqual(signal_direction(sample, "15m+5m"), "PE")
        self.assertEqual(signal_direction(sample, "5m-only"), "PE")

    def test_score_and_mandatory_checks_still_apply(self):
        sample = row("09:30", "BEARISH", "BEARISH", "BEARISH_BREAKDOWN")
        sample["score"] = "79"
        self.assertIsNone(signal_direction(sample, "5m-only"))
        sample["score"] = "90"
        sample["mandatory_checks_pass"] = "false"
        self.assertIsNone(signal_direction(sample, "5m-only"))

    def test_replay_is_next_bar_entry_and_conservative_intrabar_order(self):
        rows = [
            row("09:30", "BULLISH", "BEARISH", "BEARISH_BREAKDOWN"),
            row("09:35", "BEARISH", "BEARISH", "NEUTRAL",
                pe_open=100, pe_high=125, pe_low=75, pe_close=110),
            row("09:40", "BEARISH", "BEARISH", "NEUTRAL",
                pe_open=110, pe_high=115, pe_low=105, pe_close=112),
        ]
        result = run_replay(rows, max_lookahead=2)
        five_trades = [t for t in result["trades"] if t["strategy"] == "5m-only"]
        self.assertEqual(len(five_trades), 1)
        self.assertEqual(five_trades[0]["entry"], 100.0)
        self.assertEqual(five_trades[0]["outcome"], "LOSS")
        self.assertEqual(result["summary"]["5m-only"]["trades_simulated"], 1)


if __name__ == "__main__":
    unittest.main()
