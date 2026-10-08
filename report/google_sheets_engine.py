
import os

import requests


def append_google_sheet_row(
    row: list[object],
) -> dict[str, object]:
    """Append one row to Google Sheets through a configured webhook."""

    webhook_url = os.getenv("GOOGLE_SHEETS_WEBHOOK_URL")

    if not webhook_url:
        raise RuntimeError(
            "GOOGLE_SHEETS_WEBHOOK_URL is missing."
        )

    if not row:
        raise ValueError("row cannot be empty.")

    response = requests.post(
        webhook_url,
        json={"values": row},
        timeout=20,
    )

    response.raise_for_status()

    return {
        "status": "SENT",
        "http_status": response.status_code,
    }