import unittest
from unittest.mock import Mock, patch

from trade_exit_alert_integration import TradeExitAlertIntegration


class TestTradeExitAlertIntegration(unittest.TestCase):

    @patch("trade_exit_alert_integration.TradeExitAlertManager")
    def test_valid_signal_is_forwarded_to_manager(self, manager_class):
        send_message = Mock()
        manager = manager_class.return_value
        manager.process.return_value = {"status": "SENT"}

        integration = TradeExitAlertIntegration(send_message)
        signal = {"status": "EXIT", "reason": "STOP_LOSS"}

        result = integration.on_exit_signal(signal)

        manager.process.assert_called_once_with(signal)
        self.assertEqual(result, {"status": "SENT"})

    @patch("trade_exit_alert_integration.TradeExitAlertManager")
    def test_non_dictionary_signal_returns_error(self, manager_class):
        integration = TradeExitAlertIntegration(Mock())

        result = integration.on_exit_signal("invalid")

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(
            result["reason"],
            "Signal must be a dictionary.",
        )
        manager_class.return_value.process.assert_not_called()

    @patch("trade_exit_alert_integration.TradeExitAlertManager")
    def test_none_signal_returns_error(self, manager_class):
        integration = TradeExitAlertIntegration(Mock())

        result = integration.on_exit_signal(None)

        self.assertEqual(result["status"], "ERROR")
        manager_class.return_value.process.assert_not_called()


if __name__ == "__main__":
    unittest.main()