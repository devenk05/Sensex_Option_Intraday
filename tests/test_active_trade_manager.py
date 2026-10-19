import unittest
from concurrent.futures import ThreadPoolExecutor

from Entry.active_trade_manager import ActiveTradeManager


class ActiveTradeManagerTests(unittest.TestCase):
    def test_only_one_concurrent_trade_can_be_registered(self):
        manager = ActiveTradeManager()

        def attempt(index):
            try:
                manager.start_trade({"trade_id": str(index)})
                return "started"
            except RuntimeError:
                return "blocked"

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(attempt, range(100)))

        self.assertEqual(results.count("started"), 1)
        self.assertEqual(results.count("blocked"), 99)
        self.assertTrue(manager.has_active_trade())

    def test_returned_trade_is_a_defensive_copy(self):
        manager = ActiveTradeManager()
        manager.start_trade({"trade_id": "A", "status": "ACTIVE"})

        trade = manager.get_active_trade()
        trade["status"] = "CLOSED"

        self.assertEqual(manager.get_active_trade()["status"], "ACTIVE")

    def test_update_trade_is_atomic_and_persistable_by_caller(self):
        manager = ActiveTradeManager()
        manager.start_trade({"trade_id": "A", "status": "ACTIVE"})
        updated = manager.update_trade({"telegram_status": "SENT"})
        self.assertEqual(updated["telegram_status"], "SENT")
        self.assertEqual(manager.get_active_trade()["telegram_status"], "SENT")

    def test_close_clears_active_state(self):
        manager = ActiveTradeManager()
        manager.start_trade({"trade_id": "A"})
        closed = manager.close_trade()

        self.assertEqual(closed["trade_id"], "A")
        self.assertFalse(manager.has_active_trade())
        with self.assertRaises(RuntimeError):
            manager.close_trade()


if __name__ == "__main__":
    unittest.main()
