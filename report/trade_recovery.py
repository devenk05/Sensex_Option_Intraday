
from typing import Any

from active_trade_manager import ActiveTradeManager
from trade_state_storage import TradeStateStorage


class TradeRecovery:
    """Restore a saved active trade after application restart."""

    def __init__(
        self,
        trade_manager: ActiveTradeManager,
        storage: TradeStateStorage,
    ) -> None:
        self.trade_manager = trade_manager
        self.storage = storage

    def recover(self) -> dict[str, Any] | None:
        """Load saved state and register it with the trade manager."""

        saved_trade = self.storage.load()

        if saved_trade is None:
            return None

        if self.trade_manager.has_active_trade():
            raise RuntimeError(
                "Cannot recover: an active trade is already registered."
            )

        self.trade_manager.start_trade(saved_trade)
        return saved_trade