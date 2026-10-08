from typing import Any, Dict


class TradeExitAlertFormatter:
    """Formats trade exit signals into readable alert messages."""

    @staticmethod
    def format_signal(signal: Dict[str, Any]) -> str:
        if not isinstance(signal, dict):
            raise TypeError("signal must be a dictionary.")

        status = signal.get("status", "UNKNOWN")
        reason = signal.get("reason", "No reason provided.")
        symbol = signal.get("symbol", "N/A")
        price = signal.get("current_option_price", "N/A")

        return (
            "TRADE EXIT ALERT\n"
            f"Symbol: {symbol}\n"
            f"Status: {status}\n"
            f"Current Option Price: {price}\n"
            f"Reason: {reason}"
        )