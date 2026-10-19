from typing import Any, Callable, Dict


class TradeExitSignalHandler:
    """
    Handles exit signals from the trade monitor.

    This module records and forwards exit signals only.
    It does not place or close orders.
    """

    def __init__(
        self,
        notify_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        self.notify_callback = notify_callback
        self.last_signal = None

    def handle_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(signal, dict):
            return {
                "status": "ERROR",
                "reason": "Exit signal must be a dictionary.",
            }

        if signal.get("status") != "EXIT":
            return {
                "status": "IGNORED",
                "reason": "Signal does not indicate an exit.",
            }

        callback_result = self.notify_callback(signal)
        if callback_result is False or (
            isinstance(callback_result, dict)
            and str(callback_result.get("status", "")).upper() in {"ERROR", "FAILED", "FAILURE"}
        ):
            return {
                "status": "ERROR",
                "reason": (
                    callback_result.get("reason", "Exit callback failed.")
                    if isinstance(callback_result, dict)
                    else "Exit callback failed."
                ),
                "signal": signal,
            }

        self.last_signal = signal
        return {
            "status": "HANDLED",
            "signal": signal,
            "callback_result": callback_result,
        }

    def get_last_signal(self):
        return self.last_signal