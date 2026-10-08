from pathlib import Path

ROOT = Path(r"D:\Sensex_Option_Intraday\Entry")
ROOT.mkdir(parents=True, exist_ok=True)

FILES = {
"trade_exit_alert_config.py": r'''
from dataclasses import dataclass


@dataclass(frozen=True)
class TradeExitAlertConfig:
    """Configuration for trade exit alerts."""

    enabled: bool = True
    log_enabled: bool = True
    telegram_enabled: bool = True
    retry_count: int = 3
    retry_delay_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.retry_count < 0:
            raise ValueError("retry_count cannot be negative.")

        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative.")
''',

"trade_exit_alert_controller.py": r'''
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
''',

"trade_exit_alert_deduplicator.py": r'''
from typing import Any, Dict, Optional, Tuple


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

"trade_exit_alert_formatter.py": r'''
from typing import Any, Dict


class TradeExitAlertFormatter:
    """Formats trade exit signals into readable alert messages."""

    @staticmethod
    def format_signal(signal: Dict[str, Any]) -> str:
        if not isinstance(signal, dict):
            raise TypeError("signal must be a dictionary.")

        status = signal.get("status", "UNKNOWN")
        reason = signal.get("reason", "No reason provided.")
        symbol = signal.get("symbol", "N/A")
        price = signal.get("current_option_price", "N/A")

        return (
            "TRADE EXIT ALERT\n"
            f"Symbol: {symbol}\n"
            f"Status: {status}\n"
            f"Current Option Price: {price}\n"
            f"Reason: {reason}"
        )
''',

"trade_exit_alert_integration.py": r'''
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
''',

"trade_exit_alert_logger.py": r'''
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class TradeExitAlertLogger:
    """Saves trade exit alerts as JSON Lines records."""

    def __init__(
        self,
        log_file: str = "logs/trade_exit_alerts.jsonl",
    ) -> None:
        self.log_path = Path(log_file)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(signal, dict):
            raise TypeError("signal must be a dictionary.")

        record = {
            "logged_at": datetime.now().astimezone().isoformat(),
            "signal": signal,
        }

        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    default=str,
                )
            )
            file.write("\n")

        return {
            "status": "LOGGED",
            "file": str(self.log_path),
        }
''',

"trade_exit_alert_manager.py": r'''
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
''',

"trade_exit_alert_pipeline.py": r'''
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
''',

"trade_exit_alert_runner.py": r'''
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
''',

"trade_exit_alert_sender.py": r'''
from typing import Any, Callable, Dict

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

    def send_exit_alert(
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

        message = self.formatter.format_signal(signal)
        result = self.send_message(message)

        return {
            "status": "SENT",
            "message": message,
            "send_result": result,
        }
''',

"trade_exit_alert_service.py": r'''
from typing import Any, Dict

from trade_exit_alert_logger import TradeExitAlertLogger
from trade_exit_alert_sender import TradeExitAlertSender


class TradeExitAlertService:
    """Logs and sends trade exit alerts."""

    def __init__(self, send_message) -> None:
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

        try:
            log_result = self.logger.log_signal(signal)
            send_result = self.sender.send_exit_alert(signal)

            return {
                "status": "PROCESSED",
                "log_result": log_result,
                "send_result": send_result,
            }

        except Exception as exc:
            return {
                "status": "ERROR",
                "reason": str(exc),
            }
'''
}

for name, content in FILES.items():
    path = ROOT / name
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print("RESTORED:", path)

print()
print("ALERT_MODULE_RESTORE: COMPLETE")
