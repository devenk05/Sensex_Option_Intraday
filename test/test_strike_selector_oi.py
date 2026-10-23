import unittest

from strike_selector import select_option


class TestStrikeSelectorOI(unittest.TestCase):
    def setUp(self):
        self.options = [
            {"option_type": "CE", "strike": 72000, "last_price": 100, "oi_change": 0, "interval_volume": 100, "premium_change_5m": 1.0},
            {"option_type": "CE", "strike": 72100, "last_price": 110, "oi_change": 150, "interval_volume": 500, "premium_change_5m": 2.0},
            {"option_type": "CE", "strike": 72200, "last_price": 120, "oi_change": 300, "interval_volume": 400, "premium_change_5m": 3.0},
        ]

    def test_requires_positive_oi_and_interval_volume(self):
        result = select_option(self.options, 72000, "CE", require_oi_increase=True)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["option"]["strike"], 72200)

    def test_missing_oi_build_up_returns_no_match(self):
        result = select_option(self.options[:1], 72000, "CE", require_oi_increase=True)
        self.assertEqual(result["status"], "NO_MATCH")


if __name__ == "__main__":
    unittest.main()
