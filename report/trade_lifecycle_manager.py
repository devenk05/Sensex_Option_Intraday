
from typing import Any

from active_trade_manager import ActiveTradeManager
from trade_history import TradeHistory
from trade_history_storage import TradeHistoryStorage
from trade_state_storage import TradeStateStorage


class TradeLifecycleManager:
    """Coordinate active trade closure and history persistence."""

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