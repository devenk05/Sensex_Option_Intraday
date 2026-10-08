from pathlib import Path
from shutil import copy2

ROOT = Path(r"D:\Sensex_Option_Intraday")
ENTRY = ROOT / "Entry"

def backup(path: Path) -> None:
    if path.exists():
        bak = path.with_suffix(path.suffix + ".before_ALERT_FINAL.bak")
        copy2(path, bak)
        print("BACKUP_CREATED:", bak)

# ============================================================
# 1. Missing TradeExitAlertStatus
# ============================================================
status_path = ENTRY / "trade_exit_alert_status.py"

if not status_path.exists():
    status_path.write_text(
'''from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TradeExitAlertStatus:
    """Stores the latest trade exit alert processing status."""

    status: str = "IDLE"
    message: str = ""
    updated_at: Optional[str] = None

    def update(self, status: str, message: str = "") -> None:
        self.status = status
        self.message = message
        self.updated_at = datetime.now().astimezone().isoformat()

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "message": self.message,
            "updated_at": self.updated_at,
        }
''',
        encoding="utf-8",
    )
    print("CREATED: trade_exit_alert_status.py")
else:
    print("EXISTS: trade_exit_alert_status.py")


# ============================================================
# 2. Missing TradeExitAlertDeduplicator
# ============================================================
dedup_path = ENTRY / "trade_exit_alert_deduplicator.py"

if not dedup_path.exists():
    dedup_path.write_text(
'''from typing import Any, Dict, Optional, Tuple


class TradeExitAlertDeduplicator:
    """Prevents repeated processing of the same exit signal."""

    def __init__(self) -> None:
        self._last_signal_key: Optional[Tuple[str, str, str]] = None

    def is_duplicate(self, signal: Dict[str, Any]) -> bool:
        if not isinstance(signal, dict):
            raise TypeError("signal must be a dictionary.")

        key = (
            str(signal.get("trade_id", "")),
            str(signal.get("status", "")),
            str(signal.get("reason", "")),
        )

        if key == self._last_signal_key:
            return True

        self._last_signal_key = key
        return False

    def reset(self) -> None:
        self._last_signal_key = None
''',
        encoding="utf-8",
    )
    print("CREATED: trade_exit_alert_deduplicator.py")
else:
    print("EXISTS: trade_exit_alert_deduplicator.py")


# ============================================================
# 3. Final sender implementation
# ============================================================
sender_path = ENTRY / "trade_exit_alert_sender.py"
backup(sender_path)

sender_path.write_text(
'''from typing import Any, Callable, Dict

from trade_exit_alert_formatter import TradeExitAlertFormatter


class TradeExitAlertSender:
    """
    Formats and sends trade exit alerts through a supplied callback.
    Does not place or close trades.
    """

    def __init__(
        self,
        send_message: Callable[[str], Any],
    ) -> None:
        self.send_message = send_message
        self.formatter = TradeExitAlertFormatter()

    def send_exit_alert(self, signal: Dict[str, Any]) -> Dict[str, Any]:
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

        try:
            message = self.formatter.format_signal(signal)
            result = self.send_message(message)
        except Exception as exc:
            return {
                "status": "ERROR",
                "reason": str(exc),
            }

        # Callback must indicate success.
        if result is False or result is None:
            return {
                "status": "ERROR",
                "reason": "Alert callback did not confirm delivery.",
                "send_result": result,
            }

        # When callback returns a result dictionary, inspect its status.
        if isinstance(result, dict):
            callback_status = str(result.get("status", "")).upper()

            if callback_status not in {
                "SENT",
                "SUCCESS",
                "OK",
                "PROCESSED",
            }:
                return {
                    "status": "ERROR",
                    "reason": "Alert callback reported failure.",
                    "send_result": result,
                }

        return {
            "status": "SENT",
            "message": message,
            "send_result": result,
        }
''',
    encoding="utf-8",
)
print("PATCHED: trade_exit_alert_sender.py")


# ============================================================
# 4. Final service implementation
# ============================================================
service_path = ENTRY / "trade_exit_alert_service.py"
backup(service_path)

service_path.write_text(
'''from typing import Any, Dict
import time

from trade_exit_alert_config import TradeExitAlertConfig
from trade_exit_alert_logger import TradeExitAlertLogger
from trade_exit_alert_sender import TradeExitAlertSender


class TradeExitAlertService:
    """Logs and sends trade exit alerts with configuration and retries."""

    def __init__(
        self,
        send_message,
        config: TradeExitAlertConfig | None = None,
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
                "reason": "Trade exit alert service is disabled.",
            }

        log_result = None

        # Logging is independently configurable.
        if self.config.log_enabled:
            try:
                log_result = self.logger.log_signal(signal)
            except Exception as exc:
                return {
                    "status": "ERROR",
                    "reason": f"Exit alert logging failed: {exc}",
                }

        # Telegram sending is independently configurable.
        if not self.config.telegram_enabled:
            return {
                "status": "PROCESSED",
                "reason": "Telegram sending disabled.",
                "log_result": log_result,
                "send_result": None,
            }

        # retry_count means number of retries AFTER the first attempt.
        max_attempts = int(self.config.retry_count) + 1
        last_error = None

        for attempt in range(1, max_attempts + 1):
            result = self.sender.send_exit_alert(signal)

            if result.get("status") == "SENT":
                return {
                    "status": "PROCESSED",
                    "log_result": log_result,
                    "send_result": result,
                    "attempts": attempt,
                }

            last_error = result.get(
                "reason",
                "Exit alert sending failed.",
            )

            if attempt < max_attempts and self.config.retry_delay_seconds > 0:
                time.sleep(float(self.config.retry_delay_seconds))

        return {
            "status": "ERROR",
            "reason": last_error or "Exit alert sending failed.",
            "log_result": log_result,
            "attempts": max_attempts,
        }
''',
    encoding="utf-8",
)
print("PATCHED: trade_exit_alert_service.py")


# ============================================================
# 5. Compile everything touched
# ============================================================
import py_compile

files = [
    status_path,
    dedup_path,
    sender_path,
    service_path,
]

for file_path in files:
    py_compile.compile(str(file_path), doraise=True)
    print("COMPILE_PASS:", file_path)

print()
print("TRADE_EXIT_ALERT_FINAL_FIX_DONE")
