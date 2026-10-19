"""Atomic JSON storage for closed trade history."""
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class TradeHistoryStorage:
    def __init__(self, path=None):
        project_root = Path(__file__).resolve().parent.parent
        self.path = Path(path) if path is not None else project_root / "data" / "trade_history.json"

    def save(self, trades: list[dict[str, Any]]) -> None:
        if not isinstance(trades, list) or any(not isinstance(item, dict) for item in trades):
            raise ValueError("Trade history must be a list of dictionaries.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(trades, handle, ensure_ascii=False, indent=2, default=str, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise ValueError("Persisted trade history must be a list of dictionaries.")
        return value
