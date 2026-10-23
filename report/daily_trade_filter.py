
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Any


class DailyTradeFilter:
    """Filter trade records by trade date."""

    def filter_by_date(
        self,
        trades: list[dict[str, Any]],
        target_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return trades matching the requested YYYY-MM-DD date."""

        if not isinstance(trades, list):
            raise TypeError("Trades must be provided as a list.")

        day = target_date or datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()

        try:
            date.fromisoformat(day)
        except ValueError as exc:
            raise ValueError(
                "target_date must use YYYY-MM-DD format."
            ) from exc

        filtered_trades = []

        for trade in trades:
            if not isinstance(trade, dict):
                raise TypeError("Each trade must be a dictionary.")

            trade_date = trade.get("date")
            if not trade_date:
                # Legacy closed records may only have an ISO exit_time.
                raw_time = trade.get("exit_time") or trade.get("entry_time")
                try:
                    parsed = raw_time if isinstance(raw_time, datetime) else datetime.fromisoformat(str(raw_time))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                    trade_date = parsed.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat()
                except (TypeError, ValueError):
                    trade_date = None

            if trade_date == day:
                filtered_trades.append(dict(trade))

        return filtered_trades