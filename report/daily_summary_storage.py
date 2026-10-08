
import json
from pathlib import Path
from typing import Any


class DailySummaryStorage:
    """Save and load daily trading summaries as JSON."""

    def __init__(
        self,
        file_path: str = "data/daily_summary.json",
    ) -> None:
        self.file_path = Path(file_path)

    def save(self, summary: dict[str, Any]) -> None:
        """Persist a daily summary."""

        if not isinstance(summary, dict):
            raise TypeError("Summary must be a dictionary.")

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.file_path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(summary, file, indent=2, ensure_ascii=False)

        temp_path.replace(self.file_path)

    def load(self) -> dict[str, Any] | None:
        """Load the saved summary, or return None if absent."""

        if not self.file_path.exists():
            return None

        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Saved daily summary must be a JSON object.")

        return data

    def clear(self) -> None:
        """Delete the saved summary file if it exists."""

        if self.file_path.exists():
            self.file_path.unlink()