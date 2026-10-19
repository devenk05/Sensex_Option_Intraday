"""Durable retry queue for recommendation Telegram alerts."""
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable


class TelegramOutbox:
    def __init__(self, path=None):
        root = Path(__file__).resolve().parent.parent
        self.path = Path(path) if path is not None else root / "data" / "telegram_outbox.json"
        self._lock = threading.RLock()

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise ValueError("Telegram outbox file must contain a list of objects.")
        return data

    def _save(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(items, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def enqueue(self, alert_id: str, message: str) -> None:
        alert_id = str(alert_id or "").strip()
        if not alert_id or not isinstance(message, str) or not message.strip():
            raise ValueError("Outbox alert_id and message are required.")
        with self._lock:
            items = self._load()
            if any(str(item.get("alert_id")) == alert_id for item in items):
                return
            items.append({"alert_id": alert_id, "message": message})
            self._save(items)

    def pending_count(self) -> int:
        with self._lock:
            return len(self._load())

    def deliver_pending(self, sender: Callable[[str], Any], limit: int = 1) -> int:
        if limit < 1:
            raise ValueError("limit must be positive.")
        delivered = 0
        for _ in range(limit):
            with self._lock:
                items = self._load()
                if not items:
                    break
                item = dict(items[0])
            try:
                result = sender(item["message"])
                status = str(result.get("status", "")).upper() if isinstance(result, dict) else ""
                if status != "SENT" and not (isinstance(result, dict) and result.get("message_id") is not None):
                    print("TELEGRAM_OUTBOX_SEND_UNCONFIRMED:", item["alert_id"], result)
                    break
            except Exception as exc:
                print("TELEGRAM_OUTBOX_RETRY_PENDING:", item["alert_id"], type(exc).__name__, str(exc)[:200])
                break

            with self._lock:
                current = self._load()
                self._save([row for row in current if str(row.get("alert_id")) != item["alert_id"]])
            delivered += 1
            print("TELEGRAM_OUTBOX_DELIVERED:", item["alert_id"])
        return delivered
