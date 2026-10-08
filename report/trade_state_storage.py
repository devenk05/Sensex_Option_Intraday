
import json
from pathlib import Path
from typing import Any


class TradeStateStorage:
    """Save and load active trade state as JSON."""

    def __init__(self, file_path: str = "data/active_trade.json") -> None:
        self.file_path = Path(file_path)

    def save(self, trade: dict[str, Any] | None) -> None:
        """Persist active trade; None clears the saved state."""

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if trade is None:
            if self.file_path.exists():
                self.file_path.unlink()
            return

        if not isinstance(trade, dict):
            raise TypeError("Trade state must be a dictionary or None.")

        temp_path = self.file_path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(trade, file, indent=2, ensure_ascii=False)

        temp_path.replace(self.file_path)

    def load(self) -> dict[str, Any] | None:
        """Load saved active trade, or return None if unavailable."""

        if not self.file_path.exists():
            return None

        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data is None:
            return None

        if not isinstance(data, dict):
            raise ValueError("Saved trade state must contain a JSON object.")

        return data

    def clear(self) -> None:
        """Remove saved active trade state."""
        self.save(None)