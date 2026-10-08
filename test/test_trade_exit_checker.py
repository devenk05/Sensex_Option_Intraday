import unittest

from trade_exit_checker import TradeExitChecker


class TestTradeExitChecker(unittest.TestCase):

    def setUp(self):
        self.checker = TradeExitChecker()
        self.trade = {
            "symbol": "TEST-CE",
            "option_sl": 100,
            "option_target": 200,
        }

    def test_stop_loss_triggered(self):
        result = self.checker.check_exit(self.trade, 100)

        self.assertEqual(result["status"], "EXIT")
        self.assertEqual(result["reason"], "STOP_LOSS")

    def test_target_triggered(self):
        result = self.checker.check_exit(self.trade, 200)

        self.assertEqual(result["status"], "EXIT")
        self.assertEqual(result["reason"], "TARGET")

    def test_trade_remains_under_monitoring(self):
        result = self.checker.check_exit(self.trade, 150)

        self.assertEqual(result["status"], "MONITORING")

    def test_missing_sl_or_target(self):
        result = self.checker.check_exit(
            {"symbol": "TEST-CE"},
            150,
        )

        self.assertEqual(result["status"], "ERROR")

    def test_invalid_sl_target_order(self):
        trade = {
            "symbol": "TEST-CE",
            "option_sl": 200,
            "option_target": 100,
        }

        result = self.checker.check_exit(trade, 150)

        self.assertEqual(result["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()