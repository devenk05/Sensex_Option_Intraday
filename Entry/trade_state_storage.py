"""Persistent storage for the single active recommendation."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any


class TradeStateStorage:
    """Save, load and clear data/active_trade.json atomically."""

    def __init__(self, file_path: str | Path | None = None) -> None:
        project_root = Path(__file__).resolve().parent.parent
        self.file_path = Path(file_path) if file_path else project_root / "data" / "active_trade.json"
        self._lock = RLock()

    def load(self) -> dict[str, Any] | None:
        with self._lock:
            if not self.file_path.exists():
                return None
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Unable to load active trade from {self.file_path}: {exc}") from exc
            return dict(data) if isinstance(data, dict) and data else None

    def save(self, trade: dict[str, Any]) -> None:
        if not isinstance(trade, dict) or not trade:
            raise ValueError("Active trade must be a non-empty dictionary.")
        payload = json.dumps(trade, ensure_ascii=False, indent=2, default=str)
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

    def clear(self) -> None:
        with self._lock:
            try:
                self.file_path.unlink()
            except FileNotFoundError:
                pass
