from typing import Any

from active_trade_manager import ActiveTradeManager
from trade_history import TradeHistory
from trade_history_storage import TradeHistoryStorage
from trade_state_storage import TradeStateStorage


class TradeLifecycleManager:
    """Coordinate active trade creation, updates, closure, and persistence."""

    def __init__(
        self,
        active_trade_manager: ActiveTradeManager,
        trade_state_storage: TradeStateStorage,
        trade_history: TradeHistory,
        trade_history_storage: TradeHistoryStorage,
    ) -> None:
        self.active_trade_manager = active_trade_manager
        self.trade_state_storage = trade_state_storage
        self.trade_history = trade_history
        self.trade_history_storage = trade_history_storage

    def create_active_trade(
        self,
        trade: dict[str, Any],
    ) -> dict[str, Any]:
        """Create one active trade and persist its state."""

        if self.active_trade_manager.has_active_trade():
            raise RuntimeError("An active trade already exists.")

        if not isinstance(trade, dict) or not trade:
            raise ValueError("Trade data must be a non-empty dictionary.")

        self.active_trade_manager.start_trade(trade)

        try:
            self.trade_state_storage.save(trade)
        except Exception:
            self.active_trade_manager.close_trade()
            raise

        return dict(trade)

    def update_active_trade(
        self,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Update the active trade and persist the updated state."""

        current_trade = self.active_trade_manager.get_active_trade()

        if current_trade is None:
            raise RuntimeError("No active trade to update.")

        if not isinstance(updates, dict) or not updates:
            raise ValueError("Trade updates must be a non-empty dictionary.")

        updated_trade = dict(current_trade)
        updated_trade.update(updates)

        # Persist first so an unsuccessful save does not alter in-memory state.
        self.trade_state_storage.save(updated_trade)
        self.active_trade_manager.update_trade(updates)

        return updated_trade

    def close_active_trade(
        self,
        close_details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Close the active trade and persist the updated history."""

        active_trade = self.active_trade_manager.get_active_trade()

        if active_trade is None:
            raise RuntimeError("No active trade to close.")

        closed_trade = dict(active_trade)

        if close_details:
            closed_trade.update(close_details)

        self.trade_history.add_trade(closed_trade)

        self.trade_history_storage.save(
            self.trade_history.get_all_trades()
        )

        self.active_trade_manager.close_trade()
        self.trade_state_storage.clear()

        return closed_trade
