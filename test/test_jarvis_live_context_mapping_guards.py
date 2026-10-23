"""Regression guards for JARVIS live context wiring.

Synthetic/AST-only: no live Kite, network, Telegram, or broker actions.
"""
import ast
import unittest
from pathlib import Path

from AgenticAI.agent_orchestrator import build_review


ROOT = Path(__file__).resolve().parents[1]


def _live_dispatch_context():
    source = (ROOT / "Entry" / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    target = next(
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_evaluate_live_setup_on_completed_5m"
    )
    calls = [
        node for node in ast.walk(target)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "dispatch_agent_review"
    ]
    if len(calls) != 1 or len(calls[0].args) != 1:
        raise AssertionError("Expected one dispatch_agent_review(context_dict) call")
    context = calls[0].args[0]
    if not isinstance(context, ast.Dict):
        raise AssertionError("JARVIS dispatch argument must be a dictionary")
    return {
        key.value: value
        for key, value in zip(context.keys, context.values)
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }


class JarvisLiveContextMappingTests(unittest.TestCase):
    def test_live_dispatch_passes_required_context_fields(self):
        context = _live_dispatch_context()
        required = {
            "decision", "entry_score", "minimum_score", "market_analysis",
            "candle_structure", "multi_timeframe", "price_action",
            "cepe_comparison", "active_trade", "option_chain_available",
            "risk_limit_inr",
        }
        self.assertTrue(required.issubset(context), f"Missing fields: {sorted(required - set(context))}")

    def test_decision_context_values_are_wired_to_live_analysis_variables(self):
        context = _live_dispatch_context()
        expected_names = {
            "decision": "CURRENT_SETUP_DECISION",
            "entry_score": "entry_score",
            "market_analysis": "market_analysis",
            "candle_structure": "candle_structure",
            "multi_timeframe": "multi_timeframe",
            "price_action": "price_action",
            "cepe_comparison": "cepe_comparison",
        }
        for key, expected_name in expected_names.items():
            with self.subTest(field=key):
                value = context[key]
                self.assertIsInstance(value, ast.Name, f"{key} should be a direct live variable")
                self.assertEqual(value.id, expected_name)

    def test_live_dispatch_is_5m_only_and_advisory_remains_separate(self):
        context = _live_dispatch_context()
        self.assertNotIn("one_minute_confirmed", context)
        # The deterministic decision and advisory review must both remain present.
        source = (ROOT / "Entry" / "main.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        target = next(
            node for node in module.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_evaluate_live_setup_on_completed_5m"
        )
        calls = [
            node for node in ast.walk(target)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        call_names = {call.func.id for call in calls}
        self.assertIn("run_locked_decision_flow", call_names)
        self.assertIn("dispatch_agent_review", call_names)

    def test_synthetic_context_is_preserved_in_advisory_review(self):
        context = {
            "decision": {"status": "TRADE_CANDIDATE", "candidate": {"symbol": "SENSEX_TEST_PE", "direction": "PE"}},
            "entry_score": 88,
            "minimum_score": 80,
            "market_analysis": {"trend": "DOWN"},
            "candle_structure": {"trend": "BEARISH"},
            "multi_timeframe": {"status": "OK", "direction": "BEARISH"},
            "price_action": {"signal": "BEARISH_CONTINUATION"},
            "cepe_comparison": {"status": "OK", "candidate_direction": "PE"},
            "active_trade": False,
            "option_chain_available": True,
                        "risk_limit_inr": 1000,
        }
        review = build_review(context)
        self.assertEqual(review["mode"], "ADVISORY_ONLY")
        self.assertEqual(review["market_intelligence"]["market_trend"], "DOWN")
        self.assertEqual(review["market_intelligence"]["multi_timeframe"]["direction"], "BEARISH")
        self.assertEqual(review["market_intelligence"]["candidate_direction"], "PE")
        self.assertEqual(review["decision_audit"]["entry_score"], 88.0)
        self.assertFalse(review["risk_review"]["broker_orders_enabled"])
        self.assertTrue(review["risk_review"]["recommendation_only"])


if __name__ == "__main__":
    unittest.main()
