
import os

from kiteconnect import KiteConnect


def create_kite_client() -> KiteConnect:
    """Create and return an authenticated Zerodha Kite client."""

    api_key = os.getenv("KITE_API_KEY")
    access_token = os.getenv("KITE_ACCESS_TOKEN")

    if not api_key:
        raise RuntimeError("KITE_API_KEY is missing from environment.")

    if not access_token:
        raise RuntimeError("KITE_ACCESS_TOKEN is missing from environment.")

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    return kite
