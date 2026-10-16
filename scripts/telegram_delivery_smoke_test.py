"""Optional Telegram delivery smoke test. Sends exactly one test message when opted in."""
import json
import os
import urllib.parse
import urllib.request

def main():
    if os.getenv("SEND_TELEGRAM_TEST", "false").lower() != "true":
        print("TELEGRAM_SMOKE_TEST: SKIPPED (explicit opt-in not enabled)")
        return 0
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("TELEGRAM_SMOKE_TEST: FAIL — Telegram credentials are not configured.")
        return 2
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": "Sensex_Option_Intraday connectivity test: Telegram delivery verified. No trade/order was placed."
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data=data,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        if response.status != 200 or not result.get("ok"):
            print("TELEGRAM_SMOKE_TEST: FAIL — API rejected the test message.")
            return 1
        print("TELEGRAM_SMOKE_TEST: PASS; message_id =", result.get("result", {}).get("message_id"))
        return 0
    except Exception as exc:
        print("TELEGRAM_SMOKE_TEST: FAIL;", type(exc).__name__, str(exc)[:200])
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
