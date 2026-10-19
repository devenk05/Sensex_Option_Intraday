import unittest

from Entry.risk_manager import calculate_stop_loss


class StructuralStopLossTests(unittest.TestCase):
    def test_ce_uses_structural_reversal_even_when_over_50_points(self):
        result = calculate_stop_loss(
            entry_price=1000,
            direction="CE",
            recent_reversal_level=920,
        )
        self.assertEqual(result["stop_loss"], 920)
        self.assertEqual(result["sl_points"], 80)
        self.assertTrue(result["structural_sl_used"])
        self.assertTrue(result["risk_exceeds_50_points"])
        self.assertIsNone(result["max_sl_points"])

    def test_pe_uses_structural_reversal_even_when_over_50_points(self):
        result = calculate_stop_loss(
            entry_price=70000,
            direction="PE",
            recent_reversal_level=70080,
        )
        self.assertEqual(result["stop_loss"], 70080)
        self.assertEqual(result["sl_points"], 80)
        self.assertTrue(result["risk_exceeds_50_points"])

    def test_rejects_reversal_on_wrong_side(self):
        with self.assertRaises(ValueError):
            calculate_stop_loss(1000, "CE", 1000)
        with self.assertRaises(ValueError):
            calculate_stop_loss(70000, "PE", 70000)

    def test_rejects_invalid_direction(self):
        with self.assertRaises(ValueError):
            calculate_stop_loss(1000, "CALL", 900)


if __name__ == "__main__":
    unittest.main()
