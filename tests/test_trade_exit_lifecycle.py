import unittest

from trade_exit_checker import TradeExitChecker
from trade_exit_monitor_loop import TradeExitMonitorLoop


class TradeExitLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.trade = {
            "trade_id": "T-1",
            "symbol": "SENSEXTESTCE",
            "option_sl": 150.0,
            "option_target": 250.0,
        }

    def test_stop_loss_and_target_are_detected_at_boundary(self):
        checker = TradeExitChecker()
        self.assertEqual(checker.check_exit(self.trade, 150.0)["reason"], "STOP_LOSS")
        self.assertEqual(checker.check_exit(self.trade, 250.0)["reason"], "TARGET")
        self.assertEqual(checker.check_exit(self.trade, 200.0)["status"], "MONITORING")

    def test_exit_signal_is_dispatched_once_for_trade(self):
        calls = []
        loop = TradeExitMonitorLoop(
            get_active_trade=lambda: self.trade,
            get_current_option_price=lambda _trade: 250.0,
            on_exit_signal=calls.append,
            interval_seconds=1,
        )
        first = loop.run_once()
        second = loop.run_once()
        self.assertTrue(first["exit_signal_dispatched"])
        self.assertFalse(second["exit_signal_dispatched"])
        self.assertEqual(len(calls), 1)

    def test_quote_failure_is_propagated_from_single_tick_for_loop_to_catch(self):
        loop = TradeExitMonitorLoop(
            get_active_trade=lambda: self.trade,
            get_current_option_price=lambda _trade: (_ for _ in ()).throw(RuntimeError("offline")),
            on_exit_signal=lambda _signal: None,
            interval_seconds=1,
        )
        with self.assertRaises(RuntimeError):
            loop.run_once()


if __name__ == "__main__":
    unittest.main()
