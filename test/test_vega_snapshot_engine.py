from datetime import datetime
from zoneinfo import ZoneInfo

from Entry.vega_snapshot_engine import update_live_vega_snapshots

IST = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 10, 20, 10, 5, tzinfo=IST)


def _option(option_type, token, symbol):
    return {
        "instrument_token": token,
        "tradingsymbol": symbol,
        "expiry": "2026-10-29",
        "strike": 72000,
        "option_type": option_type,
    }


def _tick(price=700.0, timestamp="2026-10-20T10:04:30+05:30"):
    return {
        "last_price": price,
        "bid": price - 5,
        "ask": price + 5,
        "timestamp": timestamp,
    }


def test_first_live_sample_saves_contract_snapshots_without_direction_signal():
    result = update_live_vega_snapshots(
        {"CE": _option("CE", 1, "SENSEX26OCT72000CE"),
         "PE": _option("PE", 2, "SENSEX26OCT72000PE")},
        {1: _tick(), 2: _tick(price=690.0)},
        72000,
        now=NOW,
    )
    assert result["status"] == "OK"
    assert result["directional_signal"] is False
    assert "SENSEX26OCT72000CE" in result["snapshots"]
    assert result["ce"]["impact"]["reason"] == "SNAPSHOT_MISSING"


def test_second_sample_calculates_impact_for_same_contract():
    selected = {"CE": _option("CE", 1, "SENSEX26OCT72000CE")}
    first = update_live_vega_snapshots(selected, {1: _tick()}, 72000, now=NOW)
    later_tick = _tick(price=740.0, timestamp="2026-10-20T10:05:00+05:30")
    second = update_live_vega_snapshots(
        selected, {1: later_tick}, 72000, first["snapshots"], now=NOW
    )
    assert second["ce"]["status"] == "OK"
    assert second["ce"]["impact"]["status"] == "OK"
    assert second["ce"]["impact"]["contract"]["tradingsymbol"] == "SENSEX26OCT72000CE"


def test_stale_live_tick_is_rejected():
    result = update_live_vega_snapshots(
        {"CE": _option("CE", 1, "SENSEX26OCT72000CE")},
        {1: _tick(timestamp="2026-10-20T10:00:00+05:30")},
        72000,
        now=NOW,
    )
    assert result["status"] == "NO_DATA"
    assert result["ce"]["reason"] == "LIVE_TICK_STALE"


def test_ltp_fallback_can_supply_greeks_without_liquidity_depth():
    selected = {"CE": _option("CE", 1, "SENSEX26OCT72000CE")}
    tick = _tick()
    tick["bid"] = None
    tick["ask"] = None
    result = update_live_vega_snapshots(selected, {1: tick}, 72000, now=NOW)
    assert result["ce"]["status"] == "OK"
    assert result["ce"]["greeks_status"] == "AVAILABLE"
    assert result["ce"]["liquidity_status"] == "NO_DATA"
