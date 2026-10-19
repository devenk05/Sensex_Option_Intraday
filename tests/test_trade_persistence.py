import json
import tempfile
import unittest
from pathlib import Path

from Entry.active_trade_manager import ActiveTradeManager
from Entry.trade_recovery import TradeRecovery
from Entry.trade_state_storage import TradeStateStorage
from Entry.trade_history_storage import TradeHistoryStorage


VALID_TRADE = {
    "trade_id": "T-1",
    "status": "ACTIVE",
    "symbol": "SENSEXTESTCE",
    "instrument_token": 123,
    "direction": "CE",
    "entry": 200.0,
    "option_sl": 150.0,
    "option_target": 300.0,
}


class TradePersistenceTests(unittest.TestCase):
    def test_active_trade_survives_restart_and_is_restored_once(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "active_trade.json"
            storage = TradeStateStorage(path)
            storage.save(VALID_TRADE)

            manager = ActiveTradeManager()
            recovery = TradeRecovery(manager, storage)
            recovered = recovery.recover()

            self.assertEqual(recovered["trade_id"], "T-1")
            self.assertTrue(manager.has_active_trade())
            self.assertEqual(recovery.recover()["trade_id"], "T-1")

        # The file is isolated in a temporary directory; no repository data is touched.

    def test_missing_active_file_means_no_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            storage = TradeStateStorage(Path(temp) / "missing.json")
            self.assertIsNone(TradeRecovery(ActiveTradeManager(), storage).recover())

    def test_corrupt_or_incomplete_active_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "active_trade.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                TradeStateStorage(path).load()
            path.write_text(json.dumps({"status": "ACTIVE", "symbol": "X"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                TradeStateStorage(path).load()

    def test_trade_history_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            storage = TradeHistoryStorage(Path(temp) / "history.json")
            trades = [{"trade_id": "T-1", "result": "WIN"}]
            storage.save(trades)
            self.assertEqual(storage.load(), trades)


if __name__ == "__main__":
    unittest.main()
