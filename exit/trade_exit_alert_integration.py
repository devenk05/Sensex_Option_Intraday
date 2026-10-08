from typing import Any, Dict

from trade_exit_alert_manager import TradeExitAlertManager


class TradeExitAlertIntegration:
    """
    Connects trade exit signals to the alert manager.
    Does not place or close orders.
    """

    def __init__(self, send_message) -> None:
        self.alert_manager = TradeExitAlertManager(send_message)

    def on_exit_signal(
        self,
        signal: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(signal, dict):
            return {
                "status": "ERROR",
                "reason": "Signal must be a dictionary.",
            }

        return self.alert_manager.process(signal)