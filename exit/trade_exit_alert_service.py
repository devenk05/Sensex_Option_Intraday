import time
from typing import Any, Dict, Optional

from trade_exit_alert_config import TradeExitAlertConfig
from trade_exit_alert_logger import TradeExitAlertLogger
from trade_exit_alert_sender import TradeExitAlertSender


class TradeExitAlertService:
    """Logs and sends trade exit alerts using configured settings."""

    def __init__(
        self,
        send_message,
        config: Optional[TradeExitAlertConfig] = None,
    ) -> None:
        self.config = config or TradeExitAlertConfig()
        self.logger = TradeExitAlertLogger()
        self.sender = TradeExitAlertSender(send_message)

    def process_exit_signal(
        self,
        signal: Dict[str, Any],
    ) -> Dict[str, Any]:
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

        if not self.config.enabled:
            return {
                "status": "DISABLED",
                "reason": "Trade exit alerts are disabled by configuration.",
            }

        log_result = None
        if self.config.log_enabled:
            try:
                log_result = self.logger.log_signal(signal)
            except Exception as exc:
                log_result = {
                    "status": "ERROR",
                    "reason": str(exc),
                }

        if not self.config.telegram_enabled:
            return {
                "status": "PROCESSED",
                "log_result": log_result,
                "send_result": {
                    "status": "DISABLED",
                    "reason": "Telegram alerts are disabled by configuration.",
                },
            }

        send_result = None

        for attempt in range(self.config.retry_count + 1):
            send_result = self.sender.send_exit_alert(signal)

            if send_result.get("status") == "SENT":
                return {
                    "status": "PROCESSED",
                    "log_result": log_result,
                    "send_result": send_result,
                    "attempts": attempt + 1,
                }

            if attempt < self.config.retry_count:
                time.sleep(self.config.retry_delay_seconds)

        return {
            "status": "ERROR",
            "log_result": log_result,
            "send_result": send_result,
            "attempts": self.config.retry_count + 1,
            "reason": "Alert sending failed after configured retries.",
        }
