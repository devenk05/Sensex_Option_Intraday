
from typing import Any

from active_trade_manager import ActiveTradeManager


class TradeMonitor:
    """Read and report the current active trade status."""

    def __init__(
        self,
        trade_manager: ActiveTradeManager,
    ) -> None:
        self.trade_manager = trade_manager

    def get_status(self) -> dict[str, Any]:
        """Return whether a trade is active and its details."""

        active_trade = self.trade_manager.get_active_trade()

        if active_trade is None:
            return {
                "active": False,
                "trade": None,
            }

        return {
            "active": True,
            "trade": dict(active_trade),
        }