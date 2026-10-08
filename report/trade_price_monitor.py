
from typing import Any, Callable

from active_trade_manager import ActiveTradeManager


class TradePriceMonitor:
    """Fetch and report the latest price for an active trade."""

    def __init__(
        self,
        trade_manager: ActiveTradeManager,
        ltp_provider: Callable[[dict[str, Any]], float],
    ) -> None:
        self.trade_manager = trade_manager
        self.ltp_provider = ltp_provider

    def get_price_status(self) -> dict[str, Any] | None:
        """Return active trade details and its latest price."""

        trade = self.trade_manager.get_active_trade()

        if trade is None:
            return None

        ltp = self.ltp_provider(dict(trade))

        if isinstance(ltp, bool) or not isinstance(ltp, (int, float)):
            raise ValueError("LTP provider must return a numeric price.")

        if ltp <= 0:
            raise ValueError("LTP must be greater than zero.")

        return {
            "trade": dict(trade),
            "ltp": float(ltp),
        }