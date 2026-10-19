import tempfile
import unittest
from pathlib import Path

from report.dashboard import generate_dashboard


class DashboardGenerationTests(unittest.TestCase):
    def test_active_trade_fields_and_feed_diagnostics_are_rendered(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "index.html"
            generate_dashboard(
                {
                    "status": "TRADING",
                    "sensex_price": 72000,
                    "entry_score": 88,
                    "market_bias": "BULLISH",
                    "active_trade": {
                        "trade_id": "T-1",
                        "status": "ACTIVE",
                        "action": "BUY_CE",
                        "symbol": "SENSEXTESTCE",
                        "strike": 72000,
                        "entry": 200,
                        "option_sl": 150,
                        "option_target": 300,
                        "score": 88,
                        "risk_per_lot_inr": 750,
                    },
                    "trade_recovery": {"blocked": False, "reason": None},
                },
                output_path=str(output),
            )
            html = output.read_text(encoding="utf-8")
            self.assertIn('id="active-trade-panel"', html)
            self.assertIn("SENSEXTESTCE", html)
            self.assertIn("option_sl", html)
            self.assertIn("live-main-feed-status", html)
            self.assertIn("live-sensex30-feed-status", html)
            self.assertIn("trade-recovery-status", html)
            self.assertIn("function updateActiveTradePanel", html)


if __name__ == "__main__":
    unittest.main()
