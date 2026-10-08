
from datetime import datetime
from typing import Any

from daily_report_pipeline import DailyReportPipeline
from daily_report_dispatcher import DailyReportDispatcher


class DailyReportService:
    """Generate and dispatch a daily trading report."""

    def __init__(
        self,
        pipeline: DailyReportPipeline,
        dispatcher: DailyReportDispatcher,
    ) -> None:
        self.pipeline = pipeline
        self.dispatcher = dispatcher

    def run(
        self,
        trades: list[dict[str, Any]],
        report_date: str | None = None,
    ) -> dict[str, Any]:
        """Generate the report, then dispatch it."""

        report = self.pipeline.run(
            trades=trades,
            report_date=report_date,
        )

        delivery_results = self.dispatcher.dispatch(report)

        return {
            "report": report,
            "delivery_results": delivery_results,
        }