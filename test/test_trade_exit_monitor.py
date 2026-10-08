import unittest

from trade_exit_monitor import TradeExitMonitor


class TestTradeExitMonitor(unittest.TestCase):

    def setUp(self):
        self.monitor = TradeExitMonitor()
        self.trade = {
            "symbol": "TEST-CE",
            "option_sl": 100,
            "option_target": 200,
        }

    def test_stop_loss_signal(self):
        result = self.monitor.monitor_trade(self.trade, 100)

        self.assertEqual(result["status"], "EXIT")
        self.assertEqual(result["reason"], "STOP_LOSS")

    def test_target_signal(self):
        result = self.monitor.monitor_trade(self.trade, 200)

        self.assertEqual(result["status"], "EXIT")
        self.assertEqual(result["reason"], "TARGET")

    def test_monitoring_status(self):
        result = self.monitor.monitor_trade(self.trade, 150)

        self.assertEqual(result["status"], "MONITORING")

    def test_invalid_trade_data(self):
        result = self.monitor.monitor_trade(None, 150)

        self.assertEqual(result["status"], "ERROR")

    def test_invalid_price(self):
        result = self.monitor.monitor_trade(self.trade, 0)

        self.assertEqual(result["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()