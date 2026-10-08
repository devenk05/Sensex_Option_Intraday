from dataclasses import dataclass
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
