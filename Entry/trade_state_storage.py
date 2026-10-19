"""Atomic JSON persistence for the single active trade recommendation."""
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class TradeStateStorage:
    def __init__(self, path=None):
        project_root = Path(__file__).resolve().parent.parent
        self.path = Path(path) if path is not None else project_root / "data" / "active_trade.json"

    def save(self, trade: dict[str, Any]) -> None:
        if not isinstance(trade, dict) or not trade:
            raise ValueError("Active trade must be a non-empty dictionary.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(trade, handle, ensure_ascii=False, indent=2, default=str, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        with self.path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict) or not value:
            raise ValueError("Persisted active trade is not a non-empty JSON object.")
        if str(value.get("status", "ACTIVE")).upper() != "ACTIVE":
            raise ValueError("Persisted active trade is not marked ACTIVE.")
        required = ("symbol", "instrument_token", "entry", "option_sl", "option_target", "direction")
        missing = [key for key in required if value.get(key) is None]
        if missing:
            raise ValueError("Persisted active trade missing required fields: " + ", ".join(missing))
        return value

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
