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
            if self.deduplicator.has_processed(signal):
                return {
                    "status": "DUPLICATE",
                    "reason": "Exit alert was already delivered successfully.",
                }
        except Exception as exc:
            return {
                "status": "ERROR",
                "reason": f"Deduplication failed: {exc}",
            }

        result = self.alert_service.process_exit_signal(signal)
        # Failed/disabled sends are not marked as delivered: the next monitor
        # tick must be able to retry. Only successful delivery is deduplicated.
        if isinstance(result, dict) and result.get("status") == "PROCESSED":
            send_result = result.get("send_result") or {}
            if str(send_result.get("status", "")).upper() == "SENT":
                self.deduplicator.mark_processed(signal)
        return result
