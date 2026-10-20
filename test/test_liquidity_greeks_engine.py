from datetime import date, timedelta

from Entry.liquidity_greeks_engine import analyze_liquidity_greeks


def _base_option(**overrides):
    option = {
        "bid": 695.0,
        "ask": 705.0,
        "last_price": 700.0,
        "spot": 72000.0,
        "strike": 72000.0,
        "option_type": "CE",
        "expiry": date.today() + timedelta(days=30),
    }
    option.update(overrides)
    return option


def test_valid_bid_ask_produces_liquidity_and_model_greeks():
    result = analyze_liquidity_greeks(_base_option())

    assert result["status"] == "OK"
    assert result["liquidity_score"] is not None
    assert result["greeks_method"] == "BLACK_SCHOLES_ESTIMATE"
    assert result["greeks_status"] == "AVAILABLE"
    assert result["iv_price_source"] == "BID_ASK_MIDPOINT"
    assert result["vega"] is not None


def test_missing_bid_ask_uses_ltp_for_greeks_but_not_liquidity():
    result = analyze_liquidity_greeks(
        _base_option(bid=None, ask=None, last_price=700.0)
    )

    assert result["status"] == "NO_DATA"
    assert result["reason"] == "VALID_BID_ASK_UNAVAILABLE"
    assert result["liquidity_passed"] is False
    assert result["liquidity_score"] is None
    assert result["iv_price_source"] == "LTP"
    assert result["greeks_status"] == "AVAILABLE"
    assert result["vega"] is not None


def test_invalid_bid_ask_does_not_prevent_ltp_greeks():
    result = analyze_liquidity_greeks(
        _base_option(bid=710.0, ask=700.0, last_price=700.0)
    )

    assert result["status"] == "NO_DATA"
    assert result["liquidity_score"] is None
    assert result["iv_price_source"] == "LTP"
    assert result["greeks_status"] == "AVAILABLE"


def test_missing_ltp_and_bid_ask_keeps_greeks_unavailable():
    result = analyze_liquidity_greeks(
        _base_option(bid=None, ask=None, last_price=None)
    )

    assert result["status"] == "NO_DATA"
    assert result["greeks_status"] == "UNAVAILABLE"
    assert result["vega"] is None
