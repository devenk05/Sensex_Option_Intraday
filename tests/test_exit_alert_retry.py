import unittest

from trade_exit_alert_pipeline import TradeExitAlertPipeline


class ExitAlertRetryTests(unittest.TestCase):
    def test_failed_delivery_is_not_deduplicated_and_can_retry(self):
        calls = {"count": 0}

        def sender(_message):
            calls["count"] += 1
            if calls["count"] <= 4:
                raise RuntimeError("temporary Telegram outage")
            return {"status": "SENT", "message_id": 99}

        pipeline = TradeExitAlertPipeline(sender)
        signal = {
            "status": "EXIT",
            "trade_id": "T-1",
            "symbol": "SENSEXTESTCE",
            "reason": "TARGET",
            "current_option_price": 250,
        }

        failed = pipeline.process(signal)
        self.assertEqual(failed["status"], "ERROR")

        delivered = pipeline.process(signal)
        self.assertEqual(delivered["status"], "PROCESSED")
        self.assertEqual(delivered["send_result"]["status"], "SENT")

        duplicate = pipeline.process(signal)
        self.assertEqual(duplicate["status"], "DUPLICATE")


if __name__ == "__main__":
    unittest.main()
