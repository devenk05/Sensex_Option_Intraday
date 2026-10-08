
from datetime import datetime
from typing import Any

from daily_report_runner import DailyReportRunner
from daily_report_sender import DailyReportSender


class DailyReportDelivery:
    """Generate and send a daily report when it is due."""

    def __init__(
        self,
        runner: DailyReportRunner,
        sender: DailyReportSender,
    ) -> None:
        self.runner = runner
        self.sender = sender

    def deliver_if_due(
        self,
        trades: list[dict[str, Any]],
        now: datetime | None = None,
    ) -> dict[str, Any] | None:
        """Generate and send the report when the schedule is due."""

        report = self.runner.run_if_due(
            trades=trades,
            now=now,
        )

        if report is None:
            return None

        self.sender.send_report(report)
        return report