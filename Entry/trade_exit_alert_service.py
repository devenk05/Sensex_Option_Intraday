import time
from typing import Any, Dict, Optional

from trade_exit_alert_config import TradeExitAlertConfig
from trade_exit_alert_logger import TradeExitAlertLogger
from trade_exit_alert_sender import TradeExitAlertSender


class TradeExitAlertService:
    """Logs and sends trade exit alerts."""

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

        # Complete service disabled.
        if not self.config.enabled:
            return {
                "status": "DISABLED",
                "reason": "Trade exit alert service is disabled.",
                "log_result": {
                    "status": "DISABLED",
                    "reason": "Logging skipped because service is disabled.",
                },
                "send_result": {
                    "status": "DISABLED",
                    "reason": "Telegram sending skipped because service is disabled.",
                },
            }

        # Logging.
        if self.config.log_enabled:
            try:
                log_result = self.logger.log_signal(signal)
            except Exception as exc:
                log_result = {
                    "status": "ERROR",
                    "reason": str(exc),
                }
        else:
            log_result = {
                "status": "DISABLED",
                "reason": "Logging disabled by configuration.",
            }

        # Telegram disabled.
        if not self.config.telegram_enabled:
            return {
                "status": "PROCESSED",
                "log_result": log_result,
                "send_result": {
                    "status": "DISABLED",
                    "reason": "Telegram alerts disabled by configuration.",
                },
            }

        # First attempt + configured retries.
        total_attempts = int(self.config.retry_count) + 1

        last_send_result = {
            "status": "ERROR",
            "reason": "Telegram alert was not sent.",
        }

        for attempt in range(total_attempts):
            try:
                last_send_result = self.sender.send_exit_alert(signal)
            except Exception as exc:
                last_send_result = {
                    "status": "ERROR",
                    "reason": str(exc),
                }

            if last_send_result.get("status") == "SENT":
                return {
                    "status": "PROCESSED",
                    "log_result": log_result,
                    "send_result": last_send_result,
                }

            # Always call sleep between attempts,
            # including when delay is exactly 0.
            if attempt < total_attempts - 1:
                time.sleep(float(self.config.retry_delay_seconds))

        return {
            "status": "ERROR",
            "reason": last_send_result.get(
                "reason",
                "Telegram alert sending failed.",
            ),
            "log_result": log_result,
            "send_result": last_send_result,
        }
