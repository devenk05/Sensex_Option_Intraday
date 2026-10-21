from report.dashboard import _trade_setup


def test_trade_setup_uses_option_sl_target_and_live_ltp():
    html = _trade_setup({
        "action": "BUY CALL",
        "symbol": "SENSEX26OCT75000CE",
        "strike": 75000,
        "entry": 100.0,
        "option_sl": 82.5,
        "option_target": 140.0,
        "score": 88,
        "current_ltp": 125.0,
    })

    assert "₹82.50" in html
    assert "₹140.00" in html
    assert "₹125.00" in html
    assert "+25.00" in html
    assert "WAITING FOR LIVE TICK" not in html


def test_trade_setup_shows_waiting_when_live_ltp_is_unavailable():
    html = _trade_setup({
        "action": "BUY PUT",
        "symbol": "SENSEX26OCT75000PE",
        "strike": 75000,
        "entry": 100.0,
        "option_sl": 82.5,
        "option_target": 140.0,
        "score": 84,
        "current_ltp": None,
    })

    assert "WAITING FOR LIVE TICK" in html
    assert "₹82.50" in html
    assert "₹140.00" in html
    assert "+0.00" not in html


def test_trade_setup_does_not_invent_an_active_trade():
    html = _trade_setup(None)
    assert "No Active Trade" in html
    assert "Current LTP" not in html
