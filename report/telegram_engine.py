import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Load the project-root .env even when this module is imported from another
# working directory. Existing process environment variables keep precedence.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)


def send_telegram_message(message: str) -> dict[str, object]:
    """Send a text message using the Telegram Bot API."""

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing.")

    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID is missing.")

    if not message.strip():
        raise ValueError("Telegram message cannot be empty.")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=15,
    )

    response.raise_for_status()
    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            "Telegram API did not confirm message delivery."
        )

    return {
        "status": "SENT",
        "message_id": result["result"]["message_id"],
    }
