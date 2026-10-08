
from typing import Any


class DailyReportFormatter:
    """Format a daily trading report as readable text."""

    def format(self, report: dict[str, Any]) -> str:
        if not isinstance(report, dict):
            raise TypeError("Report must be a dictionary.")

        report_date = report.get("date", "Unknown date")
        total_trades = report.get("total_trades", 0)
        wins = report.get("wins", 0)
        losses = report.get("losses", 0)
        breakeven = report.get("breakeven", 0)
        win_rate = report.get("win_rate_percent", 0)
        total_pnl = report.get("total_pnl", 0)

        try:
            total_pnl_value = float(total_pnl)
            win_rate_value = float(win_rate)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid numeric value in report.") from exc

        return (
            f"📊 Daily Trading Report\n"
            f"Date: {report_date}\n"
            f"----------------------\n"
            f"Total Trades: {total_trades}\n"
            f"Wins: {wins}\n"
            f"Losses: {losses}\n"
            f"Breakeven: {breakeven}\n"
            f"Win Rate: {win_rate_value:.2f}%\n"
            f"Total P&L: ₹{total_pnl_value:.2f}"
        )