
from typing import Any


class TradePnLCalculator:
    """Calculate unrealized P&L for a trade."""

    def calculate(
        self,
        trade: dict[str, Any],
        ltp: float,
    ) -> dict[str, float]:
        if not isinstance(trade, dict):
            raise TypeError("Trade must be a dictionary.")

        try:
            entry_price = float(trade["entry_price"])
            quantity = int(trade["quantity"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "Trade must contain valid entry_price and quantity."
            ) from exc

        if entry_price <= 0 or ltp <= 0:
            raise ValueError("Prices must be greater than zero.")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        direction = str(
            trade.get("direction", "BUY")
        ).strip().upper()

        if direction == "BUY":
            pnl = (ltp - entry_price) * quantity
        elif direction == "SELL":
            pnl = (entry_price - ltp) * quantity
        else:
            raise ValueError("Direction must be BUY or SELL.")

        return {
            "entry_price": entry_price,
            "ltp": float(ltp),
            "quantity": quantity,
            "unrealized_pnl": round(pnl, 2),
        }