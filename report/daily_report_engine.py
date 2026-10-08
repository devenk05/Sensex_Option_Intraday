
from datetime import date
from typing import Any

from daily_summary import DailySummary
from daily_summary_storage import DailySummaryStorage


class DailyReportEngine:
    """Generate and save a daily trading report."""

    def __init__(
        self,
        summary_engine: DailySummary,
        summary_storage: DailySummaryStorage,
    ) -> None:
        self.summary_engine = summary_engine
        self.summary_storage = summary_storage

    def generate_report(
        self,
        trades: list[dict[str, Any]],
        report_date: str | None = None,
    ) -> dict[str, Any]:
        """Generate a report for the supplied day's trades."""

        day = report_date or date.today().isoformat()

        summary = self.summary_engine.generate(trades)

        report = {
            "date": day,
            **summary,
        }

        self.summary_storage.save(report)
        return report