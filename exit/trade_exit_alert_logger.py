import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class TradeExitAlertLogger:
    """Saves trade exit alerts as JSON Lines records."""

    def __init__(self, log_file: str = "logs/trade_exit_alerts.jsonl") -> None:
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
            file.write(json.dumps(record, ensure_ascii=False, default=str))
            file.write("\n")

        return {
            "status": "LOGGED",
            "file": str(self.log_path),
        }