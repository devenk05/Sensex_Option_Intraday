
from datetime import datetime
from typing import Any

from daily_report_engine import DailyReportEngine
from daily_report_scheduler import DailyReportScheduler


class DailyReportRunner:
    """Run daily report generation when scheduled time is reached."""

    def __init__(
        self,
        scheduler: DailyReportScheduler,
        report_engine: DailyReportEngine,
    ) -> None:
        self.scheduler = scheduler
        self.report_engine = report_engine
        self._last_run_date: str | None = None

    def run_if_due(
        self,
        trades: list[dict[str, Any]],
        now: datetime | None = None,
    ) -> dict[str, Any] | None:
        """Generate at most one report per date when due."""

        current = now or datetime.now(self.scheduler.TIMEZONE)

        if not self.scheduler.should_run(current):
            return None

        report_date = current.astimezone(
            self.scheduler.TIMEZONE
        ).date().isoformat()

        if self._last_run_date == report_date:
            return None

        report = self.report_engine.generate_report(
            trades=trades,
            report_date=report_date,
        )

        self._last_run_date = report_date
        return report