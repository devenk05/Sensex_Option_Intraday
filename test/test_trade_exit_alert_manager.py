import unittest
from unittest.mock import patch

from trade_exit_alert_manager import TradeExitAlertManager


class TestTradeExitAlertManager(unittest.TestCase):

    def setUp(self):
        self.manager = TradeExitAlertManager(
            send_message=lambda message: "MOCK_SENT"
        )

    def test_exit_signal_is_forwarded(self):
        signal = {
            "status": "EXIT",
            "symbol": "TEST-CE",
            "reason": "STOP_LOSS",
        }

        with patch.object(
            self.manager.controller,
            "handle_exit_signal",
            return_value={"status": "PROCESSED"},
        ) as mock_handle:
            result = self.manager.process(signal)

        mock_handle.assert_called_once_with(signal)
        self.assertEqual(result["status"], "PROCESSED")

    def test_invalid_signal_returns_error(self):
        result = self.manager.process(None)

        self.assertEqual(result["status"], "ERROR")

    def test_non_exit_signal_is_ignored(self):
        result = self.manager.process(
            {"status": "MONITORING"}
        )

        self.assertEqual(result["status"], "IGNORED")


if __name__ == "__main__":
    unittest.main()