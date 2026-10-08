
from datetime import datetime
from typing import Any

from daily_report_engine import DailyReportEngine
from daily_report_archive import DailyReportArchive
from daily_report_validator import DailyReportValidator
from daily_trade_filter import DailyTradeFilter


class DailyReportPipeline:
    """Filter, generate, validate, and archive a daily report."""

    def __init__(
        self,
        trade_filter: DailyTradeFilter,
        report_engine: DailyReportEngine,
        validator: DailyReportValidator,
        archive: DailyReportArchive,
    ) -> None:
        self.trade_filter = trade_filter
        self.report_engine = report_engine
        self.validator = validator
        self.archive = archive

    def run(
        self,
        trades: list[dict[str, Any]],
        report_date: str | None = None,
    ) -> dict[str, Any]:
        """Build and archive a report for one trading date."""

        day = report_date or datetime.now().date().isoformat()

        daily_trades = self.trade_filter.filter_by_date(
            trades,
            target_date=day,
        )

        report = self.report_engine.generate_report(
            trades=daily_trades,
            report_date=day,
        )

        self.validator.validate(report)
        self.archive.save(report)

        return report