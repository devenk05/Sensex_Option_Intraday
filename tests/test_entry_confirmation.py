import unittest

from Entry.entry_confirmation import evaluate_entry_confirmation


class EntryConfirmationTests(unittest.TestCase):
    def test_bullish_signal_confirms_when_15m_and_5m_align(self):
        result = evaluate_entry_confirmation("BULLISH", "BULLISH", "BULLISH_CONTINUATION")
        self.assertTrue(result["mtf_aligned"])
        self.assertTrue(result["entry_confirmed"])
        self.assertEqual(result["direction"], "BULLISH")

    def test_bearish_signal_confirms_when_15m_and_5m_align(self):
        result = evaluate_entry_confirmation("BEARISH", "BEARISH", "BEARISH_BREAKDOWN")
        self.assertTrue(result["entry_confirmed"])
        self.assertEqual(result["direction"], "BEARISH")

    def test_opposite_1m_signal_does_not_confirm(self):
        result = evaluate_entry_confirmation("BULLISH", "BULLISH", "BEARISH_REVERSAL")
        self.assertFalse(result["entry_confirmed"])
        self.assertEqual(result["direction"], "WAIT")

    def test_misaligned_timeframes_do_not_confirm(self):
        result = evaluate_entry_confirmation("BULLISH", "BEARISH", "BULLISH_CONTINUATION")
        self.assertFalse(result["mtf_aligned"])
        self.assertFalse(result["entry_confirmed"])

    def test_neutral_signal_does_not_confirm(self):
        result = evaluate_entry_confirmation("BULLISH", "BULLISH", "NEUTRAL")
        self.assertFalse(result["entry_confirmed"])


if __name__ == "__main__":
    unittest.main()
