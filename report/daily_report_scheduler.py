
from datetime import datetime, time
from zoneinfo import ZoneInfo


class DailyReportScheduler:
    """Check whether the daily report time has been reached."""

    TIMEZONE = ZoneInfo("Asia/Kolkata")
    REPORT_TIME = time(15, 35)

    def should_run(self, now: datetime | None = None) -> bool:
        """Return True at or after 15:35 IST on weekdays."""

        current_time = now or datetime.now(self.TIMEZONE)

        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=self.TIMEZONE)
        else:
            current_time = current_time.astimezone(self.TIMEZONE)

        if current_time.weekday() >= 5:
            return False

        return current_time.time() >= self.REPORT_TIME