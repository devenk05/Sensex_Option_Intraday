"""Read-only live price monitor for the active recommendation."""
from typing import Any, Callable


class TradePriceMonitor:
    def __init__(self, trade_manager, ltp_provider: Callable[[dict[str, Any]], float]):
        self.trade_manager = trade_manager
        self.ltp_provider = ltp_provider

    def get_price_status(self) -> dict[str, Any]:
        trade = self.trade_manager.get_active_trade()
        if not trade:
            return {"status": "NO_ACTIVE_TRADE", "active": False, "trade": None}
        price = float(self.ltp_provider(trade))
        if price <= 0:
            raise ValueError("Live option price must be greater than zero.")
        return {
            "status": "ACTIVE",
            "active": True,
            "trade_id": trade.get("trade_id"),
            "symbol": trade.get("symbol"),
            "entry": trade.get("entry"),
            "current_option_price": price,
            "option_sl": trade.get("option_sl"),
            "option_target": trade.get("option_target"),
        }
