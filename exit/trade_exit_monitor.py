from typing import Any, Dict

from trade_exit_checker import TradeExitChecker


class TradeExitMonitor:
    """Checks active trade exit conditions without placing orders."""

    def __init__(self) -> None:
        self.exit_checker = TradeExitChecker()

    def monitor_trade(
        self,
        trade: Dict[str, Any],
        current_option_price: float,
    ) -> Dict[str, Any]:

        if not isinstance(trade, dict):
            return {
                "status": "ERROR",
                "reason": "Trade data must be a dictionary.",
            }

        if current_option_price <= 0:
            return {
                "status": "ERROR",
                "reason": "Current option price must be greater than zero.",
            }

        return self.exit_checker.check_exit(
            trade=trade,
            current_option_price=current_option_price,
        )