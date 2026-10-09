from datetime import datetime
from kiteconnect import KiteTicker


LIVE_TICK_STATE = {}
LIVE_SENSEX_TICK_STATE = {}


def start_live_option_feed(kite, instrument_tokens, on_candle=None, sensex30_tokens=None, sensex_token=None):
    """
    Subscribe to selected options and build 1-minute OHLC candles.
    Send each finalized candle to the optional on_candle callback.
    Data only; no orders are placed.
    """
    if not instrument_tokens:
        raise ValueError("No instrument tokens provided.")

    ticker = KiteTicker(kite.api_key, kite.access_token)

    # SENSEX30 live stock ticks disabled.
    # Keep only selected options + SENSEX index token subscribed.
    sensex30_tokens = []

    all_tokens = list(
        dict.fromkeys(
            list(instrument_tokens)
            + ([sensex_token] if sensex_token else [])
        )
    )

    current_candles = {}
    candle_history = {token: [] for token in instrument_tokens}
    sensex_current_candle = None
    sensex_candle_history = []

    def on_connect(ws, response):
        print("WEBSOCKET_CONNECTED")
        ws.subscribe(all_tokens)
        ws.set_mode(ws.MODE_FULL, all_tokens)

        print("SUBSCRIBED_OPTION_TOKENS:", instrument_tokens)
        print("SUBSCRIBED_SENSEX30_TOKENS:", sensex30_tokens)
        print("SUBSCRIBED_SENSEX_TOKEN:", sensex_token)

    def finalize_candle(token, current):
        start_vol = current["start_cumulative_volume"]
        last_vol = current["last_cumulative_volume"]

        if start_vol is not None and last_vol is not None:
            minute_volume = max(0, last_vol - start_vol)
        else:
            minute_volume = None

        candle = {
            "instrument_token": token,
            "minute": current["minute"],
            "open": current["open"],
            "high": current["high"],
            "low": current["low"],
            "close": current["close"],
            "volume": minute_volume,
        }

        candle_history[token].append(candle)

        print(
            "CANDLE_1M",
            "TOKEN:", token,
            "TIME:", candle["minute"].strftime("%H:%M"),
            "O:", candle["open"],
            "H:", candle["high"],
            "L:", candle["low"],
            "C:", candle["close"],
            "V:", candle["volume"],
            "STORED:", len(candle_history[token]),
        )

        if on_candle is not None:
            try:
                on_candle(candle)
            except Exception as exc:
                print("CANDLE_CALLBACK_ERROR:", repr(exc))

    def on_ticks(ws, ticks):
        nonlocal sensex_current_candle
        for tick in ticks:
            token = tick.get("instrument_token")
            price = tick.get("last_price")
            cumulative_volume = tick.get("volume_traded")

            if token is None or price is None:
                continue

            # =====================================================
            # SENSEX INDEX LIVE TICK
            # Same WebSocket as option and Sensex 30 feed
            # =====================================================
            if sensex_token is not None and token == sensex_token:
                ohlc = tick.get("ohlc") or {}

                LIVE_SENSEX_TICK_STATE.update({
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
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

                now = datetime.now()
                minute = now.replace(second=0, microsecond=0)

                if sensex_current_candle is None:
                    sensex_current_candle = {
                        "instrument_token": token,
                        "minute": minute,
                        "open": price,
                        "high": price,
                        "low": price,
                        "close": price,
                        "volume": cumulative_volume,
                    }
                elif minute > sensex_current_candle["minute"]:
                    sensex_candle_history.append(dict(sensex_current_candle))
                    print(
                        "SENSEX_CANDLE_1M",
                        "TIME:", sensex_current_candle["minute"].strftime("%H:%M"),
                        "O:", sensex_current_candle["open"],
                        "H:", sensex_current_candle["high"],
                        "L:", sensex_current_candle["low"],
                        "C:", sensex_current_candle["close"],
                    )

                    if on_candle is not None:
                        try:
                            on_candle(dict(sensex_current_candle))
                        except Exception as exc:
                            print("SENSEX_CANDLE_CALLBACK_ERROR:", repr(exc))
                    sensex_current_candle = {
                        "instrument_token": token,
                        "minute": minute,
                        "open": price,
                        "high": price,
                        "low": price,
                        "close": price,
                        "volume": cumulative_volume,
                    }
                else:
                    sensex_current_candle["high"] = max(
                        sensex_current_candle["high"], price
                    )
                    sensex_current_candle["low"] = min(
                        sensex_current_candle["low"], price
                    )
                    sensex_current_candle["close"] = price
                    sensex_current_candle["volume"] = cumulative_volume

                print(
                    "SENSEX_LIVE_TICK",
                    "TOKEN:", token,
                    "LTP:", price,
                )
                continue
            # =====================================================
            # SENSEX 30 LIVE STOCK TICK
            # Same WebSocket as option feed
            # =====================================================
            if token in sensex30_tokens:
                from MarketData.sensex30_live_feed import LIVE_STOCK_TICK_STATE

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
                    "volume_traded": cumulative_volume,
                    "timestamp": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }

                print(
                    "SENSEX30_LIVE_TICK",
                    "TOKEN:", token,
                    "LTP:", price,
                )

                continue

            # =====================================================
            # OPTION LIVE TICK
            # =====================================================
            depth = tick.get("depth") or {}
            buy_levels = depth.get("buy") or []
            sell_levels = depth.get("sell") or []
            best_bid_level = buy_levels[0] if buy_levels else {}
            best_ask_level = sell_levels[0] if sell_levels else {}

            def _safe_number(value):
                try:
                    return float(value) if value is not None else None
                except (TypeError, ValueError):
                    return None

            LIVE_TICK_STATE[token] = {
                "instrument_token": token,
                "last_price": price,
                "volume_traded": cumulative_volume,
                "bid": _safe_number(best_bid_level.get("price")),
                "ask": _safe_number(best_ask_level.get("price")),
                "bid_quantity": _safe_number(best_bid_level.get("quantity")),
                "ask_quantity": _safe_number(best_ask_level.get("quantity")),
                "total_bid_quantity": sum(
                    float(level.get("quantity") or 0) for level in buy_levels
                ),
                "total_ask_quantity": sum(
                    float(level.get("quantity") or 0) for level in sell_levels
                ),
                "depth_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            now = datetime.now()
            minute = now.replace(second=0, microsecond=0)
            current = current_candles.get(token)

            if current is None:
                current_candles[token] = {
                    "minute": minute,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    # The first observed candle has no prior-minute baseline,
                    # so its exact volume cannot be calculated reliably.
                    "start_cumulative_volume": None,
                    "last_cumulative_volume": cumulative_volume,
                }
                continue

            if minute > current["minute"]:
                finalize_candle(token, current)

                # volume_traded is cumulative for the trading day. Use the
                # last cumulative value from the previous candle as this
                # candle's baseline, not the first tick of the new minute.
                previous_cumulative_volume = current["last_cumulative_volume"]
                current_candles[token] = {
                    "minute": minute,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "start_cumulative_volume": previous_cumulative_volume,
                    "last_cumulative_volume": cumulative_volume,
                }
            else:
                current["high"] = max(current["high"], price)
                current["low"] = min(current["low"], price)
                current["close"] = price

                if cumulative_volume is not None:
                    current["last_cumulative_volume"] = cumulative_volume

            print("LIVE_TICK", "TOKEN:", token, "LTP:", price)

    def on_close(ws, code, reason):
        print("WEBSOCKET_CLOSED:", code, reason)

    def on_error(ws, code, reason):
        print("WEBSOCKET_ERROR:", code, reason)

    ticker.on_connect = on_connect
    ticker.on_ticks = on_ticks
    ticker.on_close = on_close
    ticker.on_error = on_error

    print("STARTING_WEBSOCKET...")
    ticker.connect()

























