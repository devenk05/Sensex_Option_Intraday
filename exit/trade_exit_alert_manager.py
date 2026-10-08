from typing import Any, Dict

from trade_exit_alert_controller import TradeExitAlertController


class TradeExitAlertManager:
    """Manages processing of trade exit alerts."""

    def __init__(self, send_message) -> None:
        self.controller = TradeExitAlertController(send_message)

    def process(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(signal, dict):
            return {
                "status": "ERROR",
                "reason": "Signal must be a dictionary.",
            }

        return self.controller.handle_exit_signal(signal)