import unittest

from trade_exit_monitor_loop import TradeExitMonitorLoop


class TestExitMonitorRetry(unittest.TestCase):
    def setUp(self):
        self.trade = {
            "trade_id": "retry-test",
            "symbol": "SENSEXTESTCE",
            "entry": 150,
            "option_sl": 100,
            "option_target": 200,
        }
        self.calls = 0

        def callback(signal):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary persistence failure")

        self.loop = TradeExitMonitorLoop(
            get_active_trade=lambda: self.trade,
            get_current_option_price=lambda trade: 100,
            on_exit_signal=callback,
            interval_seconds=0.01,
        )

    def test_failed_callback_is_retried_and_then_deduplicated(self):
        first = self.loop.run_once()
        self.assertFalse(first["exit_signal_dispatched"])
        self.assertEqual(first["reason"], "EXIT_CALLBACK_FAILED_RETRY_PENDING")
        second = self.loop.run_once()
        self.assertTrue(second["exit_signal_dispatched"])
        third = self.loop.run_once()
        self.assertFalse(third["exit_signal_dispatched"])
        self.assertEqual(self.calls, 2)


if __name__ == "__main__":
    unittest.main()
