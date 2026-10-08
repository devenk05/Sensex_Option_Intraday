import unittest

from trade_exit_alert_deduplicator import TradeExitAlertDeduplicator
from trade_exit_alert_status import TradeExitAlertStatus


class TestTradeExitAlerts(unittest.TestCase):

    def test_duplicate_signal_detection(self):
        deduplicator = TradeExitAlertDeduplicator()

        signal = {
            "trade_id": "TEST-001",
            "status": "EXIT",
            "reason": "STOP_LOSS",
        }

        self.assertFalse(deduplicator.is_duplicate(signal))
        self.assertTrue(deduplicator.is_duplicate(signal))

    def test_deduplicator_reset(self):
        deduplicator = TradeExitAlertDeduplicator()

        signal = {
            "trade_id": "TEST-002",
            "status": "EXIT",
            "reason": "TARGET",
        }

        deduplicator.is_duplicate(signal)
        deduplicator.reset()

        self.assertFalse(deduplicator.is_duplicate(signal))

    def test_alert_status_update(self):
        status = TradeExitAlertStatus()
        status.update("SENT", "Test alert")

        result = status.to_dict()

        self.assertEqual(result["status"], "SENT")
        self.assertEqual(result["message"], "Test alert")
        self.assertIsNotNone(result["updated_at"])


if __name__ == "__main__":
    unittest.main()