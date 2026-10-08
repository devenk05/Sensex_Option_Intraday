import unittest

from trade_exit_alert_sender import TradeExitAlertSender


class TestTradeExitAlertSender(unittest.TestCase):

    def setUp(self):
        self.sent_messages = []

        def mock_send_message(message):
            self.sent_messages.append(message)
            return "MOCK_SENT"

        self.sender = TradeExitAlertSender(mock_send_message)

    def test_exit_signal_is_sent(self):
        signal = {
            "status": "EXIT",
            "symbol": "TEST-CE",
            "reason": "STOP_LOSS",
            "current_option_price": 95.0,
        }

        result = self.sender.send_exit_alert(signal)

        self.assertEqual(result["status"], "SENT")
        self.assertEqual(len(self.sent_messages), 1)
        self.assertIn("TEST-CE", self.sent_messages[0])
        self.assertIn("STOP_LOSS", self.sent_messages[0])

    def test_non_exit_signal_is_ignored(self):
        signal = {
            "status": "MONITORING",
            "symbol": "TEST-CE",
        }

        result = self.sender.send_exit_alert(signal)

        self.assertEqual(result["status"], "IGNORED")
        self.assertEqual(len(self.sent_messages), 0)

    def test_invalid_signal_returns_error(self):
        result = self.sender.send_exit_alert(None)

        self.assertEqual(result["status"], "ERROR")

    def test_callback_false_returns_error(self):
        sender = TradeExitAlertSender(lambda message: False)

        result = sender.send_exit_alert({"status": "EXIT"})

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["send_result"], False)

    def test_callback_failure_dict_returns_error(self):
        sender = TradeExitAlertSender(
            lambda message: {"status": "FAILED", "reason": "Network error"}
        )

        result = sender.send_exit_alert({"status": "EXIT"})

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["send_result"]["status"], "FAILED")

    def test_callback_exception_returns_error(self):
        def failing_callback(message):
            raise RuntimeError("Send failed")

        sender = TradeExitAlertSender(failing_callback)

        result = sender.send_exit_alert({"status": "EXIT"})

        self.assertEqual(result["status"], "ERROR")
        self.assertIn("Send failed", result["reason"])


if __name__ == "__main__":
    unittest.main()
