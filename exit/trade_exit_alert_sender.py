from typing import Any, Callable, Dict

from trade_exit_alert_formatter import TradeExitAlertFormatter


class TradeExitAlertSender:
    """
    Formats and sends trade exit alerts through a supplied callback.
    Does not place or close trades.
    """

    FAILURE_STATUSES = {"ERROR", "FAILED", "FAILURE", "FAIL"}

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

        message = self.formatter.format_signal(signal)

        try:
            result = self.send_message(message)
        except Exception as exc:
            return {
                "status": "ERROR",
                "message": message,
                "reason": str(exc),
            }

        if result is False:
            return {
                "status": "ERROR",
                "message": message,
                "send_result": result,
                "reason": "Send callback returned False.",
            }

        if isinstance(result, dict):
            callback_status = str(result.get("status", "")).upper()
            if callback_status in self.FAILURE_STATUSES:
                return {
                    "status": "ERROR",
                    "message": message,
                    "send_result": result,
                    "reason": "Send callback reported failure.",
                }

        return {
            "status": "SENT",
            "message": message,
            "send_result": result,
        }
