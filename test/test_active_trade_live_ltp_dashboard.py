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

    assert "INR 82.50" in html
    assert "INR 140.00" in html
    assert "INR 125.00" in html
    assert "+25.00" in html
    assert "Entry → Current LTP" in html
    assert "Entry → SL" in html
    assert "Current LTP → SL" in html
    assert "Entry → Target" in html
    assert "Current LTP → Target" in html
    assert "17.50 pts (+17.50%)" in html
    assert "40.00 pts (+40.00%)" in html
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
    assert "INR 82.50" in html
    assert "INR 140.00" in html
    assert "+0.00" not in html


def test_trade_setup_does_not_invent_an_active_trade():
    html = _trade_setup(None)
    assert "No Active Trade" in html
    assert "Current LTP" not in html


def test_generated_dashboard_refreshes_active_trade_from_live_state(tmp_path):
    from report.dashboard import generate_dashboard

    output = tmp_path / "index.html"
    generate_dashboard(
        {
            "status": "TRADING",
            "active_trade": {
                "action": "BUY CALL",
                "symbol": "SENSEX26OCT75000CE",
                "strike": 75000,
                "entry": 100.0,
                "option_sl": 82.5,
                "option_target": 140.0,
                "score": 88,
                "current_ltp": 125.0,
            },
            "active_trade_ltp": 125.0,
            "options": [],
        },
        output_path=str(output),
    )

    html = output.read_text(encoding="utf-8")
    assert 'id="active-trade-content"' in html
    assert "function updateActiveTradeLive(data)" in html
    assert "updateActiveTradeLive(data);" in html
    assert "option_target" in html
    assert "CURRENT TRADE" in html
    assert "TRADE HISTORY" in html
    assert "function updateTradeHistory(data)" in html
    assert "trade-arrival" in html
