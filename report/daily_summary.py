
from typing import Any


class DailySummary:
    """Create a basic summary from closed trade records."""

    def generate(
        self,
        trades: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not isinstance(trades, list):
            raise TypeError("Trades must be provided as a list.")

        total_trades = len(trades)
        wins = 0
        losses = 0
        breakeven = 0
        total_pnl = 0.0

        for trade in trades:
            if not isinstance(trade, dict):
                raise TypeError("Each trade must be a dictionary.")

            result = str(trade.get("result", "")).strip().upper()

            if result in {"WIN", "TARGET", "PROFIT"}:
                wins += 1
            elif result in {"LOSS", "SL", "STOP_LOSS"}:
                losses += 1
            elif result in {"BREAKEVEN", "BE"}:
                breakeven += 1

            pnl = trade.get("pnl", 0)

            try:
                total_pnl += float(pnl)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid P&L value in trade: {pnl!r}"
                ) from exc

        win_rate = (
            (wins / total_trades) * 100
            if total_trades > 0
            else 0.0
        )

        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "breakeven": breakeven,
            "win_rate_percent": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
        }