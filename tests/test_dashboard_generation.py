import tempfile
import unittest
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

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

    def test_generated_dashboard_is_reachable_over_http(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "index.html"
            generate_dashboard(
                {
                    "status": "TRADING",
                    "sensex_price": 72000,
                    "entry_score": 88,
                    "market_bias": "BULLISH",
                    "active_trade": {
                        "trade_id": "HTTP-T-1",
                        "status": "ACTIVE",
                        "action": "BUY_CE",
                        "symbol": "SENSEX_HTTP_TEST_CE",
                        "strike": 72000,
                        "entry": 200,
                        "option_sl": 150,
                        "option_target": 300,
                        "score": 88,
                    },
                    "trade_recovery": {"blocked": False, "reason": None},
                },
                output_path=str(output),
            )

            handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(
                *args, directory=temp, **kwargs
            )
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(
                    f"http://127.0.0.1:{server.server_port}/index.html",
                    timeout=3,
                ) as response:
                    body = response.read().decode("utf-8")
                    self.assertEqual(response.status, 200)
                    self.assertIn("SENSEX_HTTP_TEST_CE", body)
                    self.assertIn('id="active-trade-panel"', body)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
