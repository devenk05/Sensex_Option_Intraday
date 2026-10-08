
import time
from datetime import datetime
from typing import Any, Callable

from daily_report_job import DailyReportJob


class DailyReportLoop:
    """Periodically check and run the daily report job."""

    def __init__(
        self,
        report_job: DailyReportJob,
        trades_provider: Callable[[], list[dict[str, Any]]],
        interval_seconds: int = 30,
    ) -> None:
        if interval_seconds < 1:
            raise ValueError("Interval must be at least 1 second.")

        self.report_job = report_job
        self.trades_provider = trades_provider
        self.interval_seconds = interval_seconds
        self._running = False

    def run_forever(self) -> None:
        """Continuously check whether the report is due."""

        self._running = True

        while self._running:
            try:
                trades = self.trades_provider()

                self.report_job.run_if_due(
                    trades=trades,
                    now=datetime.now(
                        self.report_job.scheduler.TIMEZONE
                    ),
                )

            except Exception as exc:
                print(f"Daily report loop error: {exc}")

            time.sleep(self.interval_seconds)

    def stop(self) -> None:
        """Request the loop to stop after the current wait."""
        self._running = False