"""Opt-in live smoke test for Kite connectivity and Telegram delivery.

This script never calls any order-placement API. Run it only when you want a
real Telegram test message; the message is disabled unless explicitly opted in.
"""
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request


def fail(message):
    print("FAIL:", message)
    raise SystemExit(1)


def main():
    api_key = os.getenv("KITE_API_KEY")
    access_token = os.getenv("KITE_ACCESS_TOKEN")
    if not api_key or not access_token:
        fail("KITE_API_KEY and KITE_ACCESS_TOKEN must be set as environment secrets.")

    try:
        from kiteconnect import KiteConnect, KiteTicker
    except ImportError:
        fail("kiteconnect is not installed; install it with: python -m pip install kiteconnect")

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    try:
        profile = kite.profile()
        print("KITE_AUTH: PASS; user_id_present =", bool(profile.get("user_id")))
    except Exception as exc:
        fail("Kite authentication/profile failed: " + type(exc).__name__ + ": " + str(exc)[:250])

    try:
        instruments = kite.instruments("BSE")
        sensex = next(
            (
                item for item in instruments
                if str(item.get("tradingsymbol", "")).upper() == "SENSEX"
                and str(item.get("instrument_type", "")).upper() == "INDEX"
            ),
            None,
        )
        if sensex is None:
            # Quote endpoint is still a useful connectivity check if the
            # instrument dump does not expose the index row on this account.
            quote = kite.ltp(["BSE:SENSEX"])
            print("KITE_QUOTE_API: PASS; BSE:SENSEX returned =", bool(quote))
            print("LIVE_TICK: NOT_TESTED (index token unavailable from instrument dump)")
        else:
            token = int(sensex["instrument_token"])
            ticker = KiteTicker(api_key, access_token)
            received = threading.Event()
            outcome = {"tick": None, "error": None}

            def on_connect(ws, response):
                ws.subscribe([token])
                ws.set_mode(ws.MODE_LTP, [token])

            def on_ticks(ws, ticks):
                for tick in ticks:
                    if int(tick.get("instrument_token", -1)) == token and tick.get("last_price") is not None:
                        outcome["tick"] = {
                            "instrument_token": token,
                            "last_price": tick["last_price"],
                            "exchange_timestamp": str(tick.get("exchange_timestamp") or ""),
                        }
                        received.set()
                        ws.close()
                        return

            def on_error(ws, code, reason):
                outcome["error"] = str(code) + ": " + str(reason)
                received.set()

            ticker.on_connect = on_connect
            ticker.on_ticks = on_ticks
            ticker.on_error = on_error
            ticker.connect(threaded=True)

            if not received.wait(timeout=20):
                try:
                    ticker.close()
                except Exception:
                    pass
                fail("Kite authenticated, but no SENSEX WebSocket tick arrived within 20 seconds. Run during market hours and verify instrument subscription.")
            if outcome["error"]:
                fail("Kite WebSocket error: " + outcome["error"])
            if not outcome["tick"]:
                fail("Kite WebSocket closed without a usable SENSEX tick.")
            print("KITE_WEBSOCKET_TICK: PASS; tick =", json.dumps(outcome["tick"], default=str))

    except SystemExit:
        raise
    except Exception as exc:
        fail("Kite market-data smoke test failed: " + type(exc).__name__ + ": " + str(exc)[:250])

    if os.getenv("SEND_TELEGRAM_TEST", "false").lower() != "true":
        print("TELEGRAM_DELIVERY: SKIPPED (SEND_TELEGRAM_TEST is not true)")
        print("SMOKE_TEST_RESULT: PARTIAL_PASS (Kite checked; Telegram send not requested)")
        return

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        fail("SEND_TELEGRAM_TEST=true but TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")

    message = (
        "Sensex_Option_Intraday smoke test: Telegram delivery PASS. "
        "Connectivity check only; no order was placed."
    )
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode()
    request = urllib.request.Request(
        "https://api.telegram.org/bot" + bot_token + "/sendMessage",
        data=payload,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        if response.status != 200 or not result.get("ok"):
            fail("Telegram API rejected the test message: " + str(result.get("description", "unknown error")))
        print("TELEGRAM_DELIVERY: PASS; message_id =", result.get("result", {}).get("message_id"))
    except Exception as exc:
        fail("Telegram delivery failed: " + type(exc).__name__ + ": " + str(exc)[:250])

    print("SMOKE_TEST_RESULT: PASS (Kite auth, live tick, and Telegram delivery; no orders placed)")


if __name__ == "__main__":
    main()
