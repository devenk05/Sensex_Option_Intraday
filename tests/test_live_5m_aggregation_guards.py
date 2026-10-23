import ast
import unittest
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "Entry" / "main.py"


def load_aggregator():
    source = MAIN_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_aggregate_minute_candle_into_5m"
    )
    namespace = {
        "timedelta": timedelta,
        "LIVE_5M_CURRENT": None,
        "LIVE_5M_LAST_REFRESH": None,
        "LIVE_5M_CANDLE_HISTORY": [],
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(MAIN_PATH), "exec"), namespace)
    return namespace


def candle(minute, close, volume=10):
    return {
        "instrument_token": 123,
        "minute": datetime.fromisoformat(f"2026-10-23T09:{minute:02d}:00"),
        "open": close - 1,
        "high": close + 1,
        "low": close - 2,
        "close": close,
        "volume": volume,
    }


class LiveFiveMinuteAggregationGuardTests(unittest.TestCase):
    def test_only_emits_when_all_five_distinct_minutes_are_present(self):
        ns = load_aggregator()
        for minute in range(15, 20):
            self.assertIsNone(ns["_aggregate_minute_candle_into_5m"](candle(minute, 100 + minute)))
        completed = ns["_aggregate_minute_candle_into_5m"](candle(20, 120))
        self.assertIsNotNone(completed)
        self.assertEqual(completed["minute"], datetime.fromisoformat("2026-10-23T09:15:00"))
        self.assertEqual(completed["volume"], 50)
        self.assertEqual(len(ns["LIVE_5M_CANDLE_HISTORY"]), 1)

    def test_duplicate_minute_callback_is_not_double_counted(self):
        ns = load_aggregator()
        first = candle(15, 115, volume=10)
        ns["_aggregate_minute_candle_into_5m"](first)
        ns["_aggregate_minute_candle_into_5m"](dict(first))
        self.assertEqual(ns["LIVE_5M_CURRENT"]["_minute_count"], 1)
        self.assertEqual(ns["LIVE_5M_CURRENT"]["volume"], 10)

    def test_missing_minute_rejects_bucket_and_does_not_publish_decision_candle(self):
        ns = load_aggregator()
        for minute in (15, 16, 18, 19):
            ns["_aggregate_minute_candle_into_5m"](candle(minute, 100 + minute))
        completed = ns["_aggregate_minute_candle_into_5m"](candle(20, 120))
        self.assertIsNone(completed)
        self.assertEqual(ns["LIVE_5M_CANDLE_HISTORY"], [])
        self.assertIsNone(ns["LIVE_5M_LAST_REFRESH"])


if __name__ == "__main__":
    unittest.main()
