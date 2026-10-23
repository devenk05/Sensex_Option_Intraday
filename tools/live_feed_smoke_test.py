#!/usr/bin/env python3
"""Read-only Kite WebSocket smoke test. Subscribes to one instrument and never places orders.

Run from repository root:
  python tools/live_feed_smoke_test.py --token YOUR_SENSEX_INSTRUMENT_TOKEN --seconds 60
Requires KITE_API_KEY and KITE_ACCESS_TOKEN in the environment.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from threading import Event

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token", type=int, required=True, help="Kite instrument token to observe")
    parser.add_argument("--seconds", type=int, default=60, help="Maximum test duration (default: 60)")
    args = parser.parse_args()
    if args.token <= 0:
        parser.error("--token must be a positive instrument token")
    if not 10 <= args.seconds <= 300:
        parser.error("--seconds must be between 10 and 300")

    api_key = os.getenv("KITE_API_KEY")
    access_token = os.getenv("KITE_ACCESS_TOKEN")
    if not api_key or not access_token:
        print("SMOKE_FAIL: KITE_API_KEY and KITE_ACCESS_TOKEN must be set in the environment.")
        return 2

    try:
        from kiteconnect import KiteTicker
    except Exception as exc:
        print(f"SMOKE_FAIL: KiteTicker import failed: {type(exc).__name__}: {exc}")
        return 2

    finished = Event()
    state = {"connected": False, "ticks": 0, "last_price": None, "error": None}
    ticker = KiteTicker(api_key, access_token)

    def on_connect(ws, response):
        state["connected"] = True
        print("SMOKE_CONNECTED")
        ws.subscribe([args.token])
        ws.set_mode(ws.MODE_LTP, [args.token])
        print(f"SMOKE_SUBSCRIBED token={args.token} mode=LTP")

    def on_ticks(ws, ticks):
        for tick in ticks:
            if tick.get("instrument_token") == args.token and tick.get("last_price") is not None:
                state["ticks"] += 1
                state["last_price"] = tick["last_price"]
                print(f"SMOKE_TICK count={state['ticks']} ltp={state['last_price']}")

    def on_error(ws, code, reason):
        state["error"] = f"{code}: {reason}"
        print(f"SMOKE_WEBSOCKET_ERROR {state['error']}")
        finished.set()

    def on_close(ws, code, reason):
        if not finished.is_set():
            state["error"] = f"closed {code}: {reason}"
        finished.set()

    def on_noreconnect(ws):
        state["error"] = "websocket reconnect attempts exhausted"
        finished.set()

    ticker.on_connect = on_connect
    ticker.on_ticks = on_ticks
    ticker.on_error = on_error
    ticker.on_close = on_close
    ticker.on_noreconnect = on_noreconnect

    try:
        ticker.connect(threaded=True)
        deadline = time.monotonic() + args.seconds
        while time.monotonic() < deadline and not finished.is_set():
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("SMOKE_INTERRUPTED")
    except Exception as exc:
        state["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            ticker.close()
        except Exception:
            pass

    if state["connected"] and state["ticks"] > 0 and not state["error"]:
        print(f"SMOKE_PASS connected=True ticks={state['ticks']} last_price={state['last_price']}")
        print("SMOKE_SCOPE: market-data WebSocket only; no order placement or trade recommendations.")
        return 0
    print(
        "SMOKE_FAIL "
        f"connected={state['connected']} ticks={state['ticks']} error={state['error'] or 'no matching ticks received'}"
    )
    print("Check token validity, Kite session expiry, market hours, and network access.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
