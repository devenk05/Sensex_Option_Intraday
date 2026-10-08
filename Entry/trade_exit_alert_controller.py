from typing import Any, Dict

from trade_exit_alert_runner import TradeExitAlertRunner


class TradeExitAlertController:
    """Coordinates incoming trade exit signals and alert processing."""

    def __init__(self, send_message) -> None:
        self.runner = TradeExitAlertRunner(send_message)

    def handle_exit_signal(
        self,
        signal: Dict[str, Any],
    ) -> Dict[str, Any]:
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

        return self.runner.run(signal)
