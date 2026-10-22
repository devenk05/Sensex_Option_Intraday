"""Persistent JSON storage for closed trade history."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any


class TradeHistoryStorage:
    """Load/save closed trades in data/trade_history.json."""

    def __init__(self, file_path: str | Path | None = None) -> None:
        project_root = Path(__file__).resolve().parent.parent
        self.file_path = Path(file_path) if file_path else project_root / "data" / "trade_history.json"
        self._lock = RLock()

    def load(self) -> list[dict[str, Any]]:
        with self._lock:
            if not self.file_path.exists():
                return []
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Unable to load trade history from {self.file_path}: {exc}") from exc
            if not isinstance(data, list):
                raise ValueError(f"Trade history file must contain a JSON list: {self.file_path}")
            return [dict(item) for item in data if isinstance(item, dict)]

    def save(self, trades: list[dict[str, Any]]) -> None:
        if not isinstance(trades, list):
            raise TypeError("Trade history must be a list.")
        clean = [dict(item) for item in trades if isinstance(item, dict)]
        payload = json.dumps(clean, ensure_ascii=False, indent=2, default=str)
        with self._lock:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(prefix=self.file_path.name, suffix=".tmp", dir=str(self.file_path.parent))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_name, self.file_path)
            except Exception:
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass
                raise
