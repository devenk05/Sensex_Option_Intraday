import unittest

from daily_report_dispatcher import DailyReportDispatcher
from daily_summary import DailySummary


class Sender:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    def send_report(self, report):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class TestReportingResilience(unittest.TestCase):
    def test_sheets_still_runs_when_telegram_fails(self):
        telegram = Sender(error=RuntimeError("telegram down"))
        sheets = Sender(result={"status": "OK"})
        result = DailyReportDispatcher(telegram, sheets).dispatch({"date": "2026-10-23"})
        self.assertEqual(result["telegram"]["status"], "ERROR")
        self.assertEqual(result["google_sheets"]["status"], "OK")
        self.assertEqual(sheets.calls, 1)

    def test_successful_destination_is_not_resent_when_other_fails(self):
        telegram = Sender(result={"status": "sent"})
        sheets = Sender(error=RuntimeError("sheets down"))
        dispatcher = DailyReportDispatcher(telegram, sheets)
        first = dispatcher.dispatch({"date": "2026-10-23"})
        self.assertEqual(first["telegram"]["status"], "OK")
        self.assertEqual(first["google_sheets"]["status"], "ERROR")
        sheets.error = None
        second = dispatcher.dispatch({"date": "2026-10-23"})
        self.assertEqual(second["telegram"]["status"], "SKIPPED_ALREADY_DELIVERED")
        self.assertEqual(second["google_sheets"]["status"], "OK")
        self.assertEqual(telegram.calls, 1)
        self.assertEqual(sheets.calls, 2)

    def test_summary_uses_rupee_pnl_field(self):
        result = DailySummary().generate([
            {"result": "WIN", "pnl": 2000, "pnl_points": 100},
            {"result": "LOSS", "pnl": -500, "pnl_points": -25},
        ])
        self.assertEqual(result["total_pnl"], 1500)


if __name__ == "__main__":
    unittest.main()
