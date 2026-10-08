
from typing import Any

from daily_report_sender import DailyReportSender
from daily_report_google_sheets import DailyReportGoogleSheets


class DailyReportDispatcher:
    """Dispatch a daily report to Telegram and Google Sheets."""

    def __init__(
        self,
        telegram_sender: DailyReportSender,
        google_sheets_sender: DailyReportGoogleSheets,
    ) -> None:
        self.telegram_sender = telegram_sender
        self.google_sheets_sender = google_sheets_sender

    def dispatch(self, report: dict[str, Any]) -> dict[str, Any]:
        """Send a report to configured destinations."""

        results: dict[str, Any] = {}

        results["telegram"] = self.telegram_sender.send_report(report)
        results["google_sheets"] = (
            self.google_sheets_sender.send_report(report)
        )

        return results