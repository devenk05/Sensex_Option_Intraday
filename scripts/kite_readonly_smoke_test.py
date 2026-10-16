"""Manual, read-only Kite connectivity smoke test. This module never places orders."""
import os
import sys

def main():
    key = os.getenv("KITE_API_KEY")
    token = os.getenv("KITE_ACCESS_TOKEN")
    if not key or not token:
        print("KITE_SMOKE_TEST: BLOCKED — KITE_API_KEY / KITE_ACCESS_TOKEN are not configured.")
        return 2
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=key)
        kite.set_access_token(token)
        profile = kite.profile()
        print("KITE_AUTH: PASS; profile authenticated =", bool(profile.get("user_id")))
        try:
            quote = kite.ltp(["BSE:SENSEX"])
            print("KITE_QUOTE_API: PASS; SENSEX quote returned =", bool(quote))
        except Exception as exc:
            print("KITE_QUOTE_API: FAIL;", type(exc).__name__, str(exc)[:200])
            return 1
        print("SAFETY: no order placement functions were called.")
        return 0
    except Exception as exc:
        print("KITE_SMOKE_TEST: FAIL;", type(exc).__name__, str(exc)[:200])
        return 1

if __name__ == "__main__":
    sys.exit(main())
