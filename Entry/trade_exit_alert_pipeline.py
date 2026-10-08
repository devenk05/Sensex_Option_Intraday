from typing import Any, Dict

from trade_exit_alert_service import TradeExitAlertService


class TradeExitAlertPipeline:
    """Passes exit signals to the alert service."""

    def __init__(self, send_message) -> None:
        self.alert_service = TradeExitAlertService(send_message)

    def process(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(signal, dict):
            return {
                "status": "ERROR",
                "reason": "Signal must be a dictionary.",
            }

        if signal.get("status") != "EXIT":
            return {
                "status": "IGNORED",
                "reason": "Signal is not an exit signal.",
            }

        return self.alert_service.process_exit_signal(signal)
