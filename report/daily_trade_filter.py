
from datetime import date
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

        day = target_date or date.today().isoformat()

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

            if trade_date == day:
                filtered_trades.append(dict(trade))

        return filtered_trades