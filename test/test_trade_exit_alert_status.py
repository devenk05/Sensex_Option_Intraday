	import unittest
from datetime import datetime

from trade_exit_alert_status import TradeExitAlertStatus


class TestTradeExitAlertStatus(unittest.TestCase):

    def test_default_values(self):
        status = TradeExitAlertStatus()

        self.assertEqual(status.status, "IDLE")
        self.assertEqual(status.message, "")
        self.assertIsNone(status.updated_at)

    def test_update_sets_status_and_message(self):
        status = TradeExitAlertStatus()

        status.update("SENT", "Alert sent successfully.")

        self.assertEqual(status.status, "SENT")
        self.assertEqual(status.message, "Alert sent successfully.")
        self.assertIsNotNone(status.updated_at)

    def test_updated_at_is_valid_iso_datetime(self):
        status = TradeExitAlertStatus()

        status.update("ERROR", "Test error.")

        parsed = datetime.fromisoformat(status.updated_at)

        self.assertIsNotNone(parsed.tzinfo)

    def test_to_dict_returns_expected_fields(self):
        status = TradeExitAlertStatus(
            status="SENT",
            message="Alert sent.",
            updated_at="2026-09-21T10:00:00+05:30",
        )

        result = status.to_dict()

        self.assertEqual(
            result,
            {
                "status": "SENT",
                "message": "Alert sent.",
                "updated_at": "2026-09-21T10:00:00+05:30",
            },
        )

    def test_update_overwrites_previous_status(self):
        status = TradeExitAlertStatus()

        status.update("SENT", "First alert.")
        status.update("ERROR", "Second alert failed.")

        self.assertEqual(status.status, "ERROR")
        self.assertEqual(status.message, "Second alert failed.")
        self.assertIsNotNone(status.updated_at)


if __name__ == "__main__":
    unittest.main()