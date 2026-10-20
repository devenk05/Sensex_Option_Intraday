from Entry.vega_impact_engine import analyze_vega_impact


def _snapshot(**overrides):
    value = {
        "tradingsymbol": "SENSEX26OCT72000CE",
        "expiry": "2026-10-29",
        "strike": 72000,
        "option_type": "CE",
        "timestamp": "2026-10-20T10:00:00+05:30",
        "iv": 18.0,
        "vega": 12.5,
    }
    value.update(overrides)
    return value


def test_positive_iv_change_estimates_positive_premium_impact():
    previous = _snapshot()
    current = _snapshot(timestamp="2026-10-20T10:05:00+05:30", iv=19.2, vega=12.5)

    result = analyze_vega_impact(previous, current)

    assert result["status"] == "OK"
    assert result["iv_change_points"] == 1.2
    assert result["estimated_premium_impact_points"] == 15.0
    assert result["impact_direction"] == "PREMIUM_UP"


def test_negative_iv_change_estimates_negative_premium_impact():
    result = analyze_vega_impact(
        _snapshot(),
        _snapshot(timestamp="2026-10-20T10:05:00+05:30", iv=17.0),
    )

    assert result["status"] == "OK"
    assert result["estimated_premium_impact_points"] == -12.5
    assert result["impact_direction"] == "PREMIUM_DOWN"


def test_contract_mismatch_is_rejected():
    result = analyze_vega_impact(
        _snapshot(),
        _snapshot(timestamp="2026-10-20T10:05:00+05:30", strike=72100),
    )

    assert result["status"] == "UNAVAILABLE"
    assert result["reason"] == "CONTRACT_MISMATCH"


def test_stale_or_non_increasing_snapshots_are_rejected():
    stale = analyze_vega_impact(
        _snapshot(),
        _snapshot(timestamp="2026-10-20T10:20:01+05:30"),
    )
    reversed_time = analyze_vega_impact(
        _snapshot(),
        _snapshot(timestamp="2026-10-20T09:59:00+05:30"),
    )

    assert stale["reason"] == "SNAPSHOTS_TOO_FAR_APART"
    assert reversed_time["reason"] == "TIMESTAMP_NOT_INCREASING"


def test_missing_iv_or_vega_is_non_blocking_unavailable():
    result = analyze_vega_impact(
        _snapshot(),
        _snapshot(timestamp="2026-10-20T10:05:00+05:30", iv=None),
    )

    assert result["status"] == "UNAVAILABLE"
    assert result["reason"] == "IV_OR_VEGA_UNAVAILABLE"
