from __future__ import annotations

from datetime import datetime


LIVE_STOCK_TICK_STATE = {}


def start_sensex30_live_feed(kite, instrument_tokens):
    """
    Subscribe to Sensex 30 equity instruments and maintain latest live ticks.
    Data only; no orders are placed.
    """

    if not instrument_tokens:
        raise ValueError("No Sensex 30 instrument tokens provided.")

    from kiteconnect import KiteTicker

    ticker = KiteTicker(kite.api_key, kite.access_token)

    def on_connect(ws, response):
        print("SENSEX30_WEBSOCKET_CONNECTED")
        ws.subscribe(instrument_tokens)
        ws.set_mode(ws.MODE_FULL, instrument_tokens)
        print("SENSEX30_SUBSCRIBED_TOKENS:", instrument_tokens)

    def on_ticks(ws, ticks):
        for tick in ticks:
            token = tick.get("instrument_token")
            price = tick.get("last_price")

            if token is None or price is None:
                continue

            ohlc = tick.get("ohlc") or {}

            LIVE_STOCK_TICK_STATE[token] = {
                "instrument_token": token,
                "last_price": price,
                "open": ohlc.get("open"),
                "high": ohlc.get("high"),
                "low": ohlc.get("low"),
                "last_close": ohlc.get("close"),
                "change": (
                    price - ohlc.get("close")
                    if ohlc.get("close") is not None
                    else None
                ),
                "change_percent": tick.get("change"),
                "volume_traded": tick.get("volume_traded"),
                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

    def on_close(ws, code, reason):
        print("SENSEX30_WEBSOCKET_CLOSED:", code, reason)

    def on_error(ws, code, reason):
        print("SENSEX30_WEBSOCKET_ERROR:", code, reason)

    ticker.on_connect = on_connect
    ticker.on_ticks = on_ticks
    ticker.on_close = on_close
    ticker.on_error = on_error

    print("STARTING_SENSEX30_WEBSOCKET...")
    ticker.connect(threaded=True)

