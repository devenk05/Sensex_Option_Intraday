from typing import Any, Callable, Dict

from trade_exit_alert_formatter import TradeExitAlertFormatter


class TradeExitAlertSender:
    """
    Formats and sends trade exit alerts through a supplied callback.
    Does not place or close trades.
    """

    def __init__(
        self,
        send_message: Callable[[str], Any],
    ) -> None:
        self.send_message = send_message
        self.formatter = TradeExitAlertFormatter()

    def send_exit_alert(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(signal, dict):
            return {
                "status": "ERROR",
                "reason": "Exit signal must be a dictionary.",
            }

        if signal.get("status") != "EXIT":
            return {
                "status": "IGNORED",
                "reason": "Signal is not an exit signal.",
            }

        try:
            message = self.formatter.format_signal(signal)
            result = self.send_message(message)
        except Exception as exc:
            return {
                "status": "ERROR",
                "reason": str(exc),
            }

        # Callback must indicate success.
        if result is False or result is None:
            return {
                "status": "ERROR",
                "reason": "Alert callback did not confirm delivery.",
                "send_result": result,
            }

        # When callback returns a result dictionary, inspect its status.
        if isinstance(result, dict):
            callback_status = str(result.get("status", "")).upper()

            if callback_status not in {
                "SENT",
                "SUCCESS",
                "OK",
                "PROCESSED",
            }:
                return {
                    "status": "ERROR",
                    "reason": "Alert callback reported failure.",
                    "send_result": result,
                }

        return {
            "status": "SENT",
            "message": message,
            "send_result": result,
        }
