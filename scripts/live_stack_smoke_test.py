"""Read-only live-stack smoke test for Sensex_Option_Intraday.

Run this on the PC where the app/dashboard is running, during market hours.
It checks Kite auth + one live SENSEX WebSocket tick + dashboard HTTP/JSON.
A real Telegram test is opt-in via SEND_TELEGRAM_TEST=true.
No broker order-placement API is called.
"""
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode


def fail(label, detail):
    print(f"{label}: FAIL — {detail}")
    return False


def check_dashboard():
    base = os.getenv("DASHBOARD_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
    try:
        with urlopen(base + "/index.html", timeout=5) as response:
            html = response.read().decode("utf-8", errors="replace")
            if response.status != 200 or "active-trade-panel" not in html:
                return fail("DASHBOARD_HTML", "HTTP response missing active-trade panel")
        print("DASHBOARD_HTML: PASS")
    except Exception as exc:
        return fail("DASHBOARD_HTML", f"{type(exc).__name__}: {str(exc)[:180]}")

    try:
        with urlopen(base + "/live_state.json?smoke=" + str(time.time_ns()), timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if response.status != 200 or not isinstance(data, dict):
                return fail("DASHBOARD_JSON", "HTTP response is not a JSON object")
        print("DASHBOARD_JSON: PASS; keys =", ",".join(sorted(data.keys())[:25]))
        if not any(key in data for key in ("live_sensex", "sensex", "sensex_price", "spot")):
            return fail("DASHBOARD_MARKET_STATE", "No Sensex market-state field found")
        print("DASHBOARD_MARKET_STATE: PASS")
        return True
    except Exception as exc:
        return fail("DASHBOARD_JSON", f"{type(exc).__name__}: {str(exc)[:180]}")


def check_kite():
    api_key = os.getenv("KITE_API_KEY", "").strip()
    access_token = os.getenv("KITE_ACCESS_TOKEN", "").strip()
    if not api_key or not access_token:
        return fail("KITE_AUTH", "Set KITE_API_KEY and KITE_ACCESS_TOKEN in environment")
    try:
        from kiteconnect import KiteConnect, KiteTicker
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        profile = kite.profile()
        if not profile.get("user_id"):
            return fail("KITE_AUTH", "Kite profile response has no user_id")
        print("KITE_AUTH: PASS")
    except Exception as exc:
        return fail("KITE_AUTH", f"{type(exc).__name__}: {str(exc)[:180]}")

    try:
        instruments = kite.instruments()
        instrument = next((
            item for item in instruments
            if str(item.get("tradingsymbol", "")).upper() == "SENSEX"
            and str(item.get("instrument_type", "")).upper() == "INDEX"
        ), None)
        token = int(instrument["instrument_token"]) if instrument else 0
        if not token:
            quote = kite.ltp("BSE:SENSEX").get("BSE:SENSEX", {})
            token = int(quote.get("instrument_token") or 0)
        if not token:
            return fail("KITE_LIVE_TICK", "Could not resolve SENSEX instrument token")
        ticker = KiteTicker(api_key, access_token)
        received = threading.Event()
        outcome = {"tick": None, "error": None}

        def on_connect(ws, _response):
            ws.subscribe([token])
            ws.set_mode(ws.MODE_LTP, [token])

        def on_ticks(ws, ticks):
            for tick in ticks:
                if int(tick.get("instrument_token", -1)) == token and tick.get("last_price") is not None:
                    outcome["tick"] = tick
                    received.set()
                    ws.close()
                    return

        def on_error(_ws, code, reason):
            outcome["error"] = f"{code}: {reason}"
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
            return fail("KITE_LIVE_TICK", "No SENSEX WebSocket tick within 20 seconds; run during market hours")
        if outcome["error"]:
            return fail("KITE_LIVE_TICK", outcome["error"])
        if not outcome["tick"]:
            return fail("KITE_LIVE_TICK", "WebSocket closed without a usable tick")
        tick = outcome["tick"]
        print("KITE_LIVE_TICK: PASS; token =", token, "; ltp =", tick.get("last_price"))
        return True
    except Exception as exc:
        return fail("KITE_LIVE_TICK", f"{type(exc).__name__}: {str(exc)[:180]}")


def check_telegram():
    if os.getenv("SEND_TELEGRAM_TEST", "false").lower() != "true":
        print("TELEGRAM_DELIVERY: SKIPPED (set SEND_TELEGRAM_TEST=true to send one test message)")
        return None
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return fail("TELEGRAM_DELIVERY", "SEND_TELEGRAM_TEST=true but bot token/chat id is missing")
    payload = urlencode({
        "chat_id": chat_id,
        "text": "Sensex_Option_Intraday live-stack smoke test: PASS. Connectivity only; no order placed."
    }).encode("utf-8")
    request = Request(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data=payload,
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        if response.status != 200 or not result.get("ok"):
            return fail("TELEGRAM_DELIVERY", str(result.get("description", "API rejected message")))
        print("TELEGRAM_DELIVERY: PASS; message_id =", result.get("result", {}).get("message_id"))
        return True
    except Exception as exc:
        return fail("TELEGRAM_DELIVERY", f"{type(exc).__name__}: {str(exc)[:180]}")


def main():
    print("LIVE_STACK_SMOKE_TEST: READ_ONLY; no order placement")
    results = {
        "dashboard": check_dashboard(),
        "kite": check_kite(),
        "telegram": check_telegram(),
    }
    failed = [name for name, result in results.items() if result is False]
    skipped = [name for name, result in results.items() if result is None]
    if failed:
        print("LIVE_STACK_RESULT: FAIL; failed =", ",".join(failed))
        return 1
    if skipped:
        print("LIVE_STACK_RESULT: PARTIAL_PASS; skipped =", ",".join(skipped))
        return 2
    print("LIVE_STACK_RESULT: PASS; dashboard + Kite live tick + Telegram delivery")
    return 0


if __name__ == "__main__":
    sys.exit(main())
