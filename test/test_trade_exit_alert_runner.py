import unittest
from unittest.mock import patch

from trade_exit_alert_runner import TradeExitAlertRunner


class TestTradeExitAlertRunner(unittest.TestCase):

    def setUp(self):
        self.runner = TradeExitAlertRunner(
            send_message=lambda message: "MOCK_SENT"
        )

    def test_exit_signal_runs_pipeline(self):
        signal = {
            "status": "EXIT",
            "symbol": "TEST-CE",
            "reason": "STOP_LOSS",
            "current_option_price": 95.0,
        }

        with patch.object(
            self.runner.pipeline,
            "process",
            return_value={"status": "PROCESSED"},
        ) as mock_process:
            result = self.runner.run(signal)

        mock_process.assert_called_once_with(signal)
        self.assertEqual(result["status"], "PROCESSED")

    def test_invalid_signal_returns_error(self):
        result = self.runner.run(None)

        self.assertEqual(result["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()