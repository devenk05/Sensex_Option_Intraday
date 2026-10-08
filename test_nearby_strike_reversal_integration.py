from __future__ import annotations

from datetime import datetime
from pathlib import Path
import ast
import py_compile

ROOT = Path(r"D:\Sensex_Option_Intraday")
ENTRY = ROOT / "Entry"
MAIN = ENTRY / "main.py"
ENGINE = ENTRY / "nearby_strike_reversal_engine.py"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_engine_import_and_behavior() -> None:
    import sys
    sys.path.insert(0, str(ENTRY))
    from nearby_strike_reversal_engine import NearbyStrikeReversalEngine

    engine = NearbyStrikeReversalEngine(
        swing_lookback=5,
        momentum_lookback=3,
        min_setup_strength=60,
    )

    # Underlying bearish sequence.
    for i, close in enumerate([73800, 73780, 73760, 73740, 73720, 73690, 73670]):
        engine.update_underlying({
            "instrument_token": 265,
            "open": close + 5,
            "high": close + 8,
            "low": close - 8,
            "close": close,
            "volume": None,
            "minute": datetime(2026, 9, 25, 9, 35 + i),
        })

    pe = {
        "instrument_token": 7400001,
        "option_type": "PE",
        "strike": 74000.0,
        "expiry": "2026-10-01",
        "tradingsymbol": "SENSEX74000PE",
        "last_price": 310.0,
        "oi": 100000,
    }
    ce = {
        "instrument_token": 7400002,
        "option_type": "CE",
        "strike": 74000.0,
        "expiry": "2026-10-01",
        "tradingsymbol": "SENSEX74000CE",
        "last_price": 120.0,
        "oi": 100000,
    }
    engine.register_option(pe)
    engine.register_option(ce)

    minute = 0
    result = None
    # Build history below the breakout level, then breakout and hold.
    values = [310, 312, 315, 318, 320, 323, 327, 332, 338, 346, 355]
    for value in values:
        minute += 1
        result = engine.update_option_candle(
            {
                "instrument_token": pe["instrument_token"],
                "open": value - 1,
                "high": value + 2,
                "low": value - 2,
                "close": value,
                "volume": 50000,
                "minute": datetime(2026, 9, 25, 9, 35 + minute),
            },
            pe,
            spot=73670,
        )

    assert_true(result is not None, "No engine result")
    candidate = result.get("candidate")
    assert_true(candidate is not None, "Expected PE nearby candidate")
    assert_true(candidate["direction"] == "PE", "Expected PE direction")
    assert_true(candidate["underlying_1m_direction"] == "BEARISH", "Expected bearish underlying")
    assert_true(candidate["breakout"] == "BULLISH_BREAKOUT", "Expected premium breakout")
    assert_true(candidate["setup_strength"] >= 60, "Expected sufficient setup strength")


def test_installed_files() -> None:
    if not MAIN.exists():
        print("INSTALLED_MAIN_AUDIT: SKIPPED (run installer first)")
        return
    if not ENGINE.exists():
        print("INSTALLED_ENGINE_AUDIT: SKIPPED (run installer first)")
        return

    source = MAIN.read_text(encoding="utf-8-sig")
    ast.parse(source)
    required = [
        "NearbyStrikeReversalEngine",
        "TOKEN_OPTION_META",
        "NEARBY_MONITOR",
        "NEARBY_UNDERLYING_1M:",
        "NEARBY_SUBSCRIBED_TOKENS:",
        "def _apply_nearby_candidate",
        "def _finalize_nearby_candidate",
        "one_minute_confirmed=True",
    ]
    for marker in required:
        assert_true(marker in source, f"Missing integration marker: {marker}")

    py_compile.compile(str(ENGINE), doraise=True)
    py_compile.compile(str(MAIN), doraise=True)
    print("INSTALLED_MAIN_AUDIT: PASS")
    print("INSTALLED_ENGINE_AUDIT: PASS")
    print("COMPILE_AUDIT: PASS")


if __name__ == "__main__":
    test_engine_import_and_behavior()
    test_installed_files()
    print("FINAL_NEARBY_STRIKE_INTEGRATION_TEST: PASS")
