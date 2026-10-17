import sys
from pathlib import Path

ENTRY_DIR = Path(__file__).resolve().parents[1] / "Entry"
sys.path.insert(0, str(ENTRY_DIR))

from entry_confirmation import evaluate_entry_confirmation


def test_all_bullish_confirms_call_direction():
    result = evaluate_entry_confirmation("BULLISH", "BULLISH", "BULLISH_BREAKOUT")
    assert result["entry_confirmed"] is True
    assert result["direction"] == "BULLISH"


def test_all_bearish_confirms_put_direction():
    result = evaluate_entry_confirmation("BEARISH", "BEARISH", "BEARISH_BREAKDOWN")
    assert result["entry_confirmed"] is True
    assert result["direction"] == "BEARISH"


def test_bullish_mtf_with_bearish_one_minute_waits():
    result = evaluate_entry_confirmation("BULLISH", "BULLISH", "BEARISH_BREAKDOWN")
    assert result["entry_confirmed"] is False
    assert result["direction"] == "WAIT"


def test_bearish_mtf_with_bullish_one_minute_waits():
    result = evaluate_entry_confirmation("BEARISH", "BEARISH", "BULLISH_BREAKOUT")
    assert result["entry_confirmed"] is False
    assert result["direction"] == "WAIT"


def test_mtf_disagreement_waits_even_if_one_minute_matches_15m():
    result = evaluate_entry_confirmation("BULLISH", "BEARISH", "BULLISH_BREAKOUT")
    assert result["mtf_aligned"] is False
    assert result["entry_confirmed"] is False
    assert result["direction"] == "WAIT"


def test_unknown_or_wait_signal_does_not_confirm():
    for signal in ("WAIT", "UNKNOWN", "", None):
        result = evaluate_entry_confirmation("BEARISH", "BEARISH", signal)
        assert result["entry_confirmed"] is False
        assert result["direction"] == "WAIT"
