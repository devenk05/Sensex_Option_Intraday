import unittest
from unittest.mock import patch

from trade_exit_alert_config import TradeExitAlertConfig
from trade_exit_alert_service import TradeExitAlertService


class TestTradeExitAlertService(unittest.TestCase):

    def setUp(self):
        self.sent_messages = []

        def mock_send_message(message):
            self.sent_messages.append(message)
            return "MOCK_SENT"

        self.mock_send_message = mock_send_message
        self.service = TradeExitAlertService(mock_send_message)

        self.signal = {
            "status": "EXIT",
            "symbol": "TEST-CE",
            "reason": "STOP_LOSS",
            "current_option_price": 95.0,
        }

    def test_exit_signal_is_logged_and_sent(self):
        with patch.object(
            self.service.logger,
            "log_signal",
            return_value={"status": "LOGGED"},
        ) as mock_log:
            result = self.service.process_exit_signal(self.signal)

        mock_log.assert_called_once_with(self.signal)
        self.assertEqual(result["status"], "PROCESSED")
        self.assertEqual(result["send_result"]["status"], "SENT")
        self.assertEqual(len(self.sent_messages), 1)

    def test_non_exit_signal_is_ignored(self):
        result = self.service.process_exit_signal({"status": "MONITORING"})
        self.assertEqual(result["status"], "IGNORED")
        self.assertEqual(len(self.sent_messages), 0)

    def test_invalid_signal_returns_error(self):
        result = self.service.process_exit_signal(None)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(len(self.sent_messages), 0)

    def test_disabled_config_skips_logging_and_sending(self):
        service = TradeExitAlertService(
            self.mock_send_message,
            TradeExitAlertConfig(enabled=False),
        )

        with patch.object(service.logger, "log_signal") as mock_log:
            result = service.process_exit_signal(self.signal)

        self.assertEqual(result["status"], "DISABLED")
        mock_log.assert_not_called()
        self.assertEqual(len(self.sent_messages), 0)

    def test_log_disabled_skips_logging_but_sends(self):
        service = TradeExitAlertService(
            self.mock_send_message,
            TradeExitAlertConfig(log_enabled=False),
        )

        with patch.object(service.logger, "log_signal") as mock_log:
            result = service.process_exit_signal(self.signal)

        self.assertEqual(result["status"], "PROCESSED")
        mock_log.assert_not_called()
        self.assertEqual(result["send_result"]["status"], "SENT")

    def test_telegram_disabled_skips_sending(self):
        service = TradeExitAlertService(
            self.mock_send_message,
            TradeExitAlertConfig(telegram_enabled=False),
        )

        with patch.object(
            service.logger,
            "log_signal",
            return_value={"status": "LOGGED"},
        ):
            result = service.process_exit_signal(self.signal)

        self.assertEqual(result["status"], "PROCESSED")
        self.assertEqual(result["send_result"]["status"], "DISABLED")
        self.assertEqual(len(self.sent_messages), 0)

    def test_retry_then_success(self):
        callback = unittest.mock.Mock(side_effect=[False, "MOCK_SENT"])
        service = TradeExitAlertService(
            callback,
            TradeExitAlertConfig(retry_count=2, retry_delay_seconds=0),
        )

        with patch.object(service.logger, "log_signal", return_value={"status": "LOGGED"}), \
             patch("trade_exit_alert_service.time.sleep") as mock_sleep:
            result = service.process_exit_signal(self.signal)

        self.assertEqual(result["status"], "PROCESSED")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(callback.call_count, 2)
        mock_sleep.assert_called_once_with(0)

    def test_retry_exhaustion_returns_error(self):
        callback = unittest.mock.Mock(return_value=False)
        service = TradeExitAlertService(
            callback,
            TradeExitAlertConfig(retry_count=2, retry_delay_seconds=0),
        )

        with patch.object(service.logger, "log_signal", return_value={"status": "LOGGED"}), \
             patch("trade_exit_alert_service.time.sleep"):
            result = service.process_exit_signal(self.signal)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["attempts"], 3)
        self.assertEqual(callback.call_count, 3)

    def test_zero_retries_means_one_attempt(self):
        callback = unittest.mock.Mock(return_value=False)
        service = TradeExitAlertService(
            callback,
            TradeExitAlertConfig(retry_count=0, retry_delay_seconds=0),
        )

        with patch.object(service.logger, "log_signal", return_value={"status": "LOGGED"}), \
             patch("trade_exit_alert_service.time.sleep") as mock_sleep:
            result = service.process_exit_signal(self.signal)

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["attempts"], 1)
        callback.assert_called_once()
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
