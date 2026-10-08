
from typing import Any


class DailyReportValidator:
    """Validate required fields in a daily report."""

    REQUIRED_FIELDS = {
        "date",
        "total_trades",
        "wins",
        "losses",
        "breakeven",
        "win_rate_percent",
        "total_pnl",
    }

    def validate(self, report: dict[str, Any]) -> bool:
        """Return True if the report passes basic validation."""

        if not isinstance(report, dict):
            raise TypeError("Report must be a dictionary.")

        missing_fields = self.REQUIRED_FIELDS - report.keys()

        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Missing report fields: {missing}")

        count_fields = (
            "total_trades",
            "wins",
            "losses",
            "breakeven",
        )

        for field in count_fields:
            value = report[field]

            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{field} must be an integer.")

            if value < 0:
                raise ValueError(f"{field} cannot be negative.")

        for field in ("win_rate_percent", "total_pnl"):
            try:
                float(report[field])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{field} must be numeric."
                ) from exc

        return True