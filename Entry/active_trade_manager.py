from threading import RLock
from typing import Any


class ActiveTradeManager:
    """Thread-safe in-memory manager for at most one active recommendation."""

    def __init__(self) -> None:
        self._active_trade: dict[str, Any] | None = None
        self._lock = RLock()

    def get_active_trade(self) -> dict[str, Any] | None:
        """Return a defensive copy of the active trade, if any."""
        with self._lock:
            return dict(self._active_trade) if self._active_trade is not None else None

    def has_active_trade(self) -> bool:
        """Return whether an active trade exists."""
        with self._lock:
            return self._active_trade is not None

    def start_trade(self, trade: dict[str, Any]) -> None:
        """Atomically register a trade if no trade is currently active."""
        if not isinstance(trade, dict) or not trade:
            raise ValueError("Trade data must be a non-empty dictionary.")

        with self._lock:
            if self._active_trade is not None:
                raise RuntimeError("An active trade already exists.")
            self._active_trade = dict(trade)

    def close_trade(self) -> dict[str, Any]:
        """Atomically close and return the active trade."""
        with self._lock:
            if self._active_trade is None:
                raise RuntimeError("No active trade to close.")

            closed_trade = dict(self._active_trade)
            self._active_trade = None
            return closed_trade
