from typing import Any, Dict


class TradeExitChecker:
    """
    Checks option premium against configured option SL and target.

    This checker does not place or close orders.
    """

    def check_exit(
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

        option_sl = trade.get("option_sl")
        option_target = trade.get("option_target")

        if option_sl is None or option_target is None:
            return {
                "status": "ERROR",
                "reason": "option_sl and option_target are required.",
            }

        try:
            option_sl = float(option_sl)
            option_target = float(option_target)
        except (TypeError, ValueError):
            return {
                "status": "ERROR",
                "reason": "SL and target must be numeric values.",
            }

        if option_sl <= 0 or option_target <= 0:
            return {
                "status": "ERROR",
                "reason": "SL and target must be greater than zero.",
            }

        if option_sl >= option_target:
            return {
                "status": "ERROR",
                "reason": "For a BUY option, SL must be below target.",
            }

        symbol = trade.get("symbol", "N/A")

        if current_option_price <= option_sl:
            return {
                "status": "EXIT",
                "reason": "STOP_LOSS",
                "symbol": symbol,
                "current_option_price": current_option_price,
            }

        if current_option_price >= option_target:
            return {
                "status": "EXIT",
                "reason": "TARGET",
                "symbol": symbol,
                "current_option_price": current_option_price,
            }

        return {
            "status": "MONITORING",
            "reason": "No exit condition triggered.",
            "symbol": symbol,
            "current_option_price": current_option_price,
        }