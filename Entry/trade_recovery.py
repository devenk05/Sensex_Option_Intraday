"""Restore a persisted active recommendation after a process restart."""
from typing import Any


class TradeRecovery:
    def __init__(self, trade_manager, storage):
        self.trade_manager = trade_manager
        self.storage = storage

    def recover(self) -> dict[str, Any] | None:
        if self.trade_manager.has_active_trade():
            return self.trade_manager.get_active_trade()
        trade = self.storage.load()
        if trade is None:
            return None
        self.trade_manager.start_trade(trade)
        return self.trade_manager.get_active_trade()
