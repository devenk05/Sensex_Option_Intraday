
import json
from pathlib import Path
from typing import Any


class TradeHistoryStorage:
    """Persist closed trade history in a JSON file."""

    def __init__(self, file_path: str = "data/trade_history.json") -> None:
        self.file_path = Path(file_path)

    def save(self, trades: list[dict[str, Any]]) -> None:
        """Save a list of trade records."""

        if not isinstance(trades, list):
            raise TypeError("Trades must be provided as a list.")

        if not all(isinstance(trade, dict) for trade in trades):
            raise TypeError("Every trade record must be a dictionary.")

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.file_path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(trades, file, indent=2, ensure_ascii=False)

        temp_path.replace(self.file_path)

    def load(self) -> list[dict[str, Any]]:
        """Load trade records, or return an empty list if absent."""

        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Saved trade history must be a JSON list.")

        if not all(isinstance(trade, dict) for trade in data):
            raise ValueError("Each saved trade record must be a JSON object.")

        return data

    def clear(self) -> None:
        """Delete the saved history file if it exists."""

        if self.file_path.exists():
            self.file_path.unlink()