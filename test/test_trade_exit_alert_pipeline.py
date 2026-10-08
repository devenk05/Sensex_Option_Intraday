import unittest
from unittest.mock import patch

from trade_exit_alert_pipeline import TradeExitAlertPipeline


class TestTradeExitAlertPipeline(unittest.TestCase):

    def setUp(self):
        self.sent_messages = []

        def mock_send_message(message):
            self.sent_messages.append(message)
            return "MOCK_SENT"

        self.pipeline = TradeExitAlertPipeline(mock_send_message)

    def test_exit_signal_is_processed(self):
        signal = {
            "status": "EXIT",
            "symbol": "TEST-CE",
            "reason": "STOP_LOSS",
            "current_option_price": 95.0,
        }

        with patch.object(
            self.pipeline.alert_service,
            "process_exit_signal",
            return_value={"status": "PROCESSED"},
        ) as mock_process:
            result = self.pipeline.process(signal)

        mock_process.assert_called_once_with(signal)
        self.assertEqual(result["status"], "PROCESSED")

    def test_non_exit_signal_is_ignored(self):
        signal = {
            "status": "MONITORING",
            "symbol": "TEST-CE",
        }

        result = self.pipeline.process(signal)

        self.assertEqual(result["status"], "IGNORED")

    def test_invalid_signal_returns_error(self):
        result = self.pipeline.process(None)

        self.assertEqual(result["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()