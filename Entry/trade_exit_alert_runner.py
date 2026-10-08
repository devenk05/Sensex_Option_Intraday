from typing import Any, Dict

from trade_exit_alert_pipeline import TradeExitAlertPipeline


class TradeExitAlertRunner:
    """Runs the trade exit alert pipeline for incoming signals."""

    def __init__(self, send_message) -> None:
        self.pipeline = TradeExitAlertPipeline(send_message)

    def run(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(signal, dict):
            return {
                "status": "ERROR",
                "reason": "Signal must be a dictionary.",
            }

        return self.pipeline.process(signal)
