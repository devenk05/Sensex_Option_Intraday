from typing import Any

from daily_report_sender import DailyReportSender
from daily_report_google_sheets import DailyReportGoogleSheets


class DailyReportDispatcher:
    """Dispatch independently and remember successful destinations per report date."""

    def __init__(
        self,
        telegram_sender: DailyReportSender,
        google_sheets_sender: DailyReportGoogleSheets,
    ) -> None:
        self.telegram_sender = telegram_sender
        self.google_sheets_sender = google_sheets_sender
        self._delivered: dict[str, set[str]] = {}

    @staticmethod
    def _result_ok(result: Any) -> bool:
        if result is False:
            return False
        if isinstance(result, dict) and str(result.get("status", "")).upper() in {"ERROR", "FAILED", "FAIL"}:
            return False
        return True

    def dispatch(self, report: dict[str, Any]) -> dict[str, Any]:
        """Send each destination independently and retry only failed destinations."""
        report_date = str(report.get("date") or "UNKNOWN_DATE")
        delivered = self._delivered.setdefault(report_date, set())
        results: dict[str, Any] = {}

        destinations = (
            ("telegram", self.telegram_sender),
            ("google_sheets", self.google_sheets_sender),
        )
        for name, sender in destinations:
            if name in delivered:
                results[name] = {"status": "SKIPPED_ALREADY_DELIVERED"}
                continue
            try:
                value = sender.send_report(report)
                if self._result_ok(value):
                    delivered.add(name)
                    results[name] = {"status": "OK", "result": value}
                else:
                    results[name] = {"status": "ERROR", "result": value}
            except Exception as exc:
                results[name] = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}

        return results
