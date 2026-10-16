"""Manual, read-only Kite authentication and live SENSEX WebSocket smoke test.

This module never calls an order-placement API. Run during market hours with
valid Kite credentials; a valid authentication alone is not a live-tick pass.
"""
import os
import sys
import threading


def _read_credential(name):
    value = os.getenv(name, "").strip()
    if not value:
        return None, f"{name} is empty or not configured"
    if any(char.isspace() for char in value):
        return None, f"{name} contains internal whitespace/newline characters"
    return value, None


def main():
    key, key_error = _read_credential("KITE_API_KEY")
    token, token_error = _read_credential("KITE_ACCESS_TOKEN")
    errors = [error for error in (key_error, token_error) if error]
    if errors:
        print("KITE_SMOKE_TEST: BLOCKED — " + "; ".join(errors) + ".")
        return 2

    try:
        from kiteconnect import KiteConnect, KiteTicker
        kite = KiteConnect(api_key=key)
        kite.set_access_token(token)
        profile = kite.profile()
        print("KITE_AUTH: PASS; profile authenticated =", bool(profile.get("user_id")))
    except Exception as exc:
        print("KITE_AUTH: FAIL;", type(exc).__name__, str(exc)[:200])
        return 1

    try:
        # Index rows may not be returned by the exchange-filtered instrument dump.
        instruments = kite.instruments()
        sensex = next(
            (
                item for item in instruments
                if str(item.get("tradingsymbol", "")).upper() == "SENSEX"
                and str(item.get("instrument_type", "")).upper() == "INDEX"
            ),
            None,
        )
        if sensex is not None:
            instrument_token = int(sensex["instrument_token"])
        else:
            # Fallback to the same SENSEX symbol that is already validated by kite.ltp().
            quote = kite.ltp("BSE:SENSEX").get("BSE:SENSEX", {})
            instrument_token = int(quote.get("instrument_token") or 0)
            if not instrument_token:
                print("LIVE_TICK: FAIL — Kite returned the SENSEX LTP but no instrument token was available.")
                return 1

        ticker = KiteTicker(key, token)
        received = threading.Event()
        outcome = {"tick": None, "error": None}

        def on_connect(ws, response):
            ws.subscribe([instrument_token])
            ws.set_mode(ws.MODE_LTP, [instrument_token])

        def on_ticks(ws, ticks):
            for tick in ticks:
                if int(tick.get("instrument_token", -1)) == instrument_token and tick.get("last_price") is not None:
                    outcome["tick"] = {
                        "instrument_token": instrument_token,
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
            print("LIVE_TICK: FAIL — no SENSEX WebSocket tick within 20 seconds; run during market hours.")
            return 1
        if outcome["error"]:
            print("LIVE_TICK: FAIL;", outcome["error"])
            return 1
        if not outcome["tick"]:
            print("LIVE_TICK: FAIL — WebSocket closed without a usable tick.")
            return 1

        print("LIVE_TICK: PASS; tick =", outcome["tick"])
        print("SAFETY: no order placement functions were called.")
        return 0
    except Exception as exc:
        print("LIVE_TICK: FAIL;", type(exc).__name__, str(exc)[:200])
        return 1


if __name__ == "__main__":
    sys.exit(main())
