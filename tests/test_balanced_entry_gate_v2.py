"""Regression tests for Balanced Entry Gate V2 decision-flow behavior."""

from Entry.trade_decision_flow import (
    check_pivot_points,
    check_reversal_continuation,
    compare_ce_pe,
    derive_market_bias,
)


def test_missing_volume_is_diagnostic_not_a_hard_veto():
    result = compare_ce_pe(
        market_bias="BULLISH",
        pivot_analysis=None,
        price_action={"signal": "BULLISH_CONTINUATION"},
        volume_analysis={},
        oi_summary={},
        ce={},
        pe={},
    )

    assert result["status"] == "CONFIRMED"
    assert result["direction"] == "CE"
    assert result["volume_state"] == "UNAVAILABLE_OPTIONAL"
    assert result["volume_data_unavailable"] is True


def test_measured_zero_candidate_volume_still_blocks():
    result = compare_ce_pe(
        market_bias="BULLISH",
        pivot_analysis=None,
        price_action={"signal": "BULLISH_CONTINUATION"},
        volume_analysis={},
        oi_summary={},
        ce={"volume": 0},
        pe={"volume": 0},
    )

    assert result["status"] == "NOT_CONFIRMED"
    assert result["reason"] == "CANDIDATE_OPTION_VOLUME_NOT_ACTIVE"
    assert result["volume_is_blocking"] is True


def test_clear_opposite_price_action_still_blocks_selected_side():
    result = compare_ce_pe(
        market_bias="BULLISH",
        pivot_analysis=None,
        price_action={"signal": "BEARISH_BREAKDOWN"},
        volume_analysis={},
        oi_summary={},
        ce={},
        pe={},
    )

    assert result["status"] == "NOT_CONFIRMED"
    assert result["reason"] == "PRICE_ACTION_NOT_CONFIRMED_FOR_SELECTED_SIDE"


def test_pivot_misalignment_is_not_a_standalone_reversal_veto():
    location = check_pivot_points(
        market_bias="BULLISH",
        spot=100.0,
        pivot_analysis={"pivot": 101.0},
    )
    result = check_reversal_continuation(
        market_bias="BULLISH",
        spot=100.0,
        location=location,
        price_action={"signal": "BULLISH_CONTINUATION"},
        cepe={"direction": "CE"},
    )

    assert location["status"] == "NOT_CONFIRMED"
    assert result["status"] == "CONFIRMED"
    assert result["pivot_status"] == "NOT_CONFIRMED"
    assert result["reason"].endswith("PIVOT_SUPPORTING_ONLY")


def test_explicit_mtf_mismatch_does_not_count_as_aligned():
    result = derive_market_bias(
        {
            "direction_15m": "BULLISH",
            "direction_5m": "BEARISH",
            "alignment": "ALIGNED",
        },
        {"structure": "NEUTRAL"},
    )

    assert result["bias"] == "NEUTRAL"
    assert result["status"] == "NOT_CONFIRMED"
