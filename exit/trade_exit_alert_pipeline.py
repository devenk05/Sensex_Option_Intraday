from typing import Any, Dict

from trade_exit_alert_service import TradeExitAlertService
from trade_exit_alert_deduplicator import TradeExitAlertDeduplicator


class TradeExitAlertPipeline:
    """Deduplicates exit signals before passing them to the alert service."""

    def __init__(self, send_message) -> None:
        self.alert_service = TradeExitAlertService(send_message)
        self.deduplicator = TradeExitAlertDeduplicator()

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

        try:
            if self.deduplicator.is_duplicate(signal):
                return {
                    "status": "DUPLICATE",
                    "reason": "Exit signal has already been processed.",
                }
        except Exception as exc:
            return {
                "status": "ERROR",
                "reason": f"Deduplication failed: {exc}",
            }

        return self.alert_service.process_exit_signal(signal)
