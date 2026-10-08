
from datetime import datetime, time
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("Asia/Kolkata")

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


def get_market_status(
    current_time: datetime | None = None,
) -> dict[str, str]:
    """Return market status based on Indian market session hours."""

    if current_time is None:
        current_time = datetime.now(TIMEZONE)
    elif current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=TIMEZONE)
    else:
        current_time = current_time.astimezone(TIMEZONE)

    current_clock = current_time.time()

    if MARKET_OPEN <= current_clock < MARKET_CLOSE:
        status = "TRADING"
    elif current_clock < MARKET_OPEN:
        status = "PRE_MARKET"
    else:
        status = "CLOSED"

    return {
        "status": status,
        "date": current_time.strftime("%Y-%m-%d"),
        "time": current_time.strftime("%H:%M:%S"),
        "timezone": "Asia/Kolkata",
    }