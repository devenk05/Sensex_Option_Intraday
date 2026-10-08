import unittest
from unittest.mock import patch

from trade_exit_alert_controller import TradeExitAlertController


class TestTradeExitAlertController(unittest.TestCase):

    def setUp(self):
        self.controller = TradeExitAlertController(
            send_message=lambda message: "MOCK_SENT"
        )

    def test_exit_signal_is_forwarded(self):
        signal = {
            "status": "EXIT",
            "symbol": "TEST-CE",
            "reason": "STOP_LOSS",
        }

        with patch.object(
            self.controller.runner,
            "run",
            return_value={"status": "PROCESSED"},
        ) as mock_run:
            result = self.controller.handle_exit_signal(signal)

        mock_run.assert_called_once_with(signal)
        self.assertEqual(result["status"], "PROCESSED")

    def test_non_exit_signal_is_ignored(self):
        result = self.controller.handle_exit_signal(
            {"status": "MONITORING"}
        )

        self.assertEqual(result["status"], "IGNORED")

    def test_invalid_signal_returns_error(self):
        result = self.controller.handle_exit_signal(None)

        self.assertEqual(result["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()