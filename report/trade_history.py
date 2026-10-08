
from typing import Any


class TradeHistory:
    """Store closed trade records in memory."""

    def __init__(self) -> None:
        self._trades: list[dict[str, Any]] = []

    def add_trade(self, trade: dict[str, Any]) -> None:
        """Add a closed trade record."""

        if not isinstance(trade, dict):
            raise TypeError("Trade record must be a dictionary.")

        if not trade:
            raise ValueError("Trade record cannot be empty.")

        self._trades.append(dict(trade))

    def get_all_trades(self) -> list[dict[str, Any]]:
        """Return a copy of all recorded trades."""
        return [dict(trade) for trade in self._trades]

    def get_trade_count(self) -> int:
        """Return the number of recorded trades."""
        return len(self._trades)

    def clear(self) -> None:
        """Clear all trade records from memory."""
        self._trades.clear()