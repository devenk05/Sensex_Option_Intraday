
import json
from pathlib import Path
from typing import Any


class DailyReportArchive:
    """Archive daily reports in date-named JSON files."""

    def __init__(self, archive_dir: str = "data/reports") -> None:
        self.archive_dir = Path(archive_dir)

    def save(self, report: dict[str, Any]) -> Path:
        """Save a report using its YYYY-MM-DD date."""

        if not isinstance(report, dict):
            raise TypeError("Report must be a dictionary.")

        report_date = report.get("date")

        if not isinstance(report_date, str):
            raise ValueError("Report must contain a date string.")

        from datetime import date

        try:
            date.fromisoformat(report_date)
        except ValueError as exc:
            raise ValueError(
                "Report date must use YYYY-MM-DD format."
            ) from exc

        self.archive_dir.mkdir(parents=True, exist_ok=True)

        file_path = self.archive_dir / f"{report_date}.json"
        temp_path = file_path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2, ensure_ascii=False)

        temp_path.replace(file_path)
        return file_path

    def load(self, report_date: str) -> dict[str, Any] | None:
        """Load an archived report for the given date."""

        from datetime import date

        try:
            date.fromisoformat(report_date)
        except ValueError as exc:
            raise ValueError(
                "report_date must use YYYY-MM-DD format."
            ) from exc

        file_path = self.archive_dir / f"{report_date}.json"

        if not file_path.exists():
            return None

        with file_path.open("r", encoding="utf-8") as file:
            report = json.load(file)

        if not isinstance(report, dict):
            raise ValueError("Archived report must be a JSON object.")

        return report