def calculate_ema(values, period):
    """Calculate EMA from a list of numeric values."""
    if period <= 0:
        raise ValueError("EMA period must be positive.")

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period

    for value in values[period:]:
        ema = (value * multiplier) + (ema * (1 - multiplier))

    return ema


def calculate_rsi(values, period=14):
    """Calculate RSI using Wilder's smoothing method."""
    if period <= 0:
        raise ValueError("RSI period must be positive.")

    if len(values) <= period:
        return None

    changes = [
        values[i] - values[i - 1]
        for i in range(1, len(values))
    ]

    gains = [max(change, 0) for change in changes]
    losses = [max(-change, 0) for change in changes]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(changes)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    relative_strength = avg_gain / avg_loss
    return 100 - (100 / (1 + relative_strength))


def calculate_indicators(candles):
    """Calculate EMA 5/13/26 and RSI 14 from oldest to newest candles."""
    closes = [float(candle["close"]) for candle in candles]

    ema_5 = calculate_ema(closes, 5)
    ema_13 = calculate_ema(closes, 13)
    ema_26 = calculate_ema(closes, 26)
    rsi_14 = calculate_rsi(closes, 14)

    if ema_5 is None or ema_13 is None or ema_26 is None:
        ema_alignment = "INSUFFICIENT_DATA"
    elif ema_5 > ema_13 > ema_26:
        ema_alignment = "BULLISH"
    elif ema_5 < ema_13 < ema_26:
        ema_alignment = "BEARISH"
    else:
        ema_alignment = "MIXED"

    if rsi_14 is None:
        rsi_momentum = "INSUFFICIENT_DATA"
    elif rsi_14 >= 55:
        rsi_momentum = "BULLISH"
    elif rsi_14 <= 45:
        rsi_momentum = "BEARISH"
    else:
        rsi_momentum = "NEUTRAL"

    return {
        "ema_5": ema_5,
        "ema_13": ema_13,
        "ema_26": ema_26,
        "rsi_14": rsi_14,
        "ema_alignment": ema_alignment,
        "rsi_momentum": rsi_momentum,
        "candle_count": len(closes),
    }
