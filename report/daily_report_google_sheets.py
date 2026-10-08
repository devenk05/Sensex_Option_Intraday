
from typing import Any



class DailyReportGoogleSheets:
    """Send daily report summary to Google Sheets."""

    def __init__(self, sheets_engine: Any) -> None:
        self.sheets_engine = sheets_engine

    def send_report(self, report: dict[str, Any]) -> Any:
        """Send report fields as a single row."""

        if not isinstance(report, dict):
            raise TypeError("Report must be a dictionary.")

        row = [
            report.get("date", ""),
            report.get("total_trades", 0),
            report.get("wins", 0),
            report.get("losses", 0),
            report.get("breakeven", 0),
            report.get("win_rate_percent", 0),
            report.get("total_pnl", 0),
        ]

        return self.sheets_engine.send_row(row)
