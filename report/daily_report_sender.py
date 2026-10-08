
from typing import Any

from daily_report_formatter import DailyReportFormatter



class DailyReportSender:
    """Format and send a daily report through Telegram."""

    def __init__(
        self,
        formatter: DailyReportFormatter,
        telegram_engine: Any,
    ) -> None:
        self.formatter = formatter
        self.telegram_engine = telegram_engine

    def send_report(self, report: dict[str, Any]) -> Any:
        """Format the report and send it using TelegramEngine."""

        message = self.formatter.format(report)
        return self.telegram_engine.send_message(message)
