
from datetime import datetime
from typing import Any

from daily_report_scheduler import DailyReportScheduler
from daily_report_service import DailyReportService


class DailyReportJob:
    """Check report schedule and run the daily report service."""

    def __init__(
        self,
        scheduler: DailyReportScheduler,
        report_service: DailyReportService,
    ) -> None:
        self.scheduler = scheduler
        self.report_service = report_service
        self._last_run_date: str | None = None

    def run_if_due(
        self,
        trades: list[dict[str, Any]],
        now: datetime | None = None,
    ) -> dict[str, Any] | None:
        """Run the report service once per date when due."""

        current = now or datetime.now(self.scheduler.TIMEZONE)

        if not self.scheduler.should_run(current):
            return None

        local_time = current.astimezone(self.scheduler.TIMEZONE)
        report_date = local_time.date().isoformat()

        if self._last_run_date == report_date:
            return None

        result = self.report_service.run(
            trades=trades,
            report_date=report_date,
        )

        self._last_run_date = report_date
        return result