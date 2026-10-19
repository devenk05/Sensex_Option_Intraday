import os
import time

import requests


def send_telegram_message(message: str) -> dict[str, object]:
    """Send a text message and retry transient Telegram/network failures."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing.")
    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID is missing.")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Telegram message cannot be empty.")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    last_error = None

    # Bounded retry: do not block the live decision loop indefinitely.
    for attempt in range(3):
        try:
            response = requests.post(
                url,
                json={"chat_id": chat_id, "text": message},
                timeout=10,
            )
            response.raise_for_status()
            try:
                result = response.json()
            except ValueError as exc:
                raise RuntimeError("Telegram returned invalid JSON.") from exc

            if not isinstance(result, dict) or not result.get("ok"):
                description = result.get("description") if isinstance(result, dict) else None
                raise RuntimeError(
                    "Telegram API did not confirm message delivery."
                    + (f" {description}" if description else "")
                )

            message_id = (result.get("result") or {}).get("message_id")
            if message_id is None:
                raise RuntimeError("Telegram response omitted message_id.")

            return {"status": "SENT", "message_id": message_id, "attempts": attempt + 1}

        except (requests.RequestException, RuntimeError) as exc:
            last_error = exc
            # Do not retry most permanent client errors (except rate limits).
            if isinstance(exc, requests.HTTPError):
                status = exc.response.status_code if exc.response is not None else None
                if status is not None and 400 <= status < 500 and status != 429:
                    break
            if attempt < 2:
                time.sleep(attempt + 1)

    raise RuntimeError(f"Telegram delivery failed after bounded retries: {last_error}") from last_error
