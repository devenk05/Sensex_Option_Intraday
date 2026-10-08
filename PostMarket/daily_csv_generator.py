from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any


class DailyCSVGenerator:
    """
    Creates one CSV archive for the current trading day.

    Intended execution:
        15:35 IST, after the 15:30 market close.
    """

    TIMEZONE = "Asia/Kolkata"

    def __init__(self, output_dir: str | Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[1]

        self.output_dir = (
            Path(output_dir)
            if output_dir
            else project_root / "data" / "daily"
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        rows: list[dict[str, Any]],
        report_date: str | None = None,
    ) -> Path:
        """
        Create the daily CSV.

        report_date format:
            YYYY-MM-DD

        Returns:
            Path of the generated CSV file.
        """

        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        file_path = self.output_dir / f"{report_date}.csv"

        if not rows:
            rows = [{
                "DATE": report_date,
                "STATUS": "NO_TRADE_DATA",
            }]

        headers: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in headers:
                    headers.append(key)

        with file_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=headers,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(rows)

        print("DAILY_CSV_CREATED:", file_path)

        return file_path


if __name__ == "__main__":
    generator = DailyCSVGenerator()

    generator.generate(
        rows=[],
        report_date=datetime.now().strftime("%Y-%m-%d"),
    )
