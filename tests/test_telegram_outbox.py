import tempfile
import unittest
from pathlib import Path

from Entry.telegram_outbox import TelegramOutbox


class TelegramOutboxTests(unittest.TestCase):
    def test_failed_delivery_stays_queued_then_success_removes_it(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = TelegramOutbox(Path(temp) / "outbox.json")
            outbox.enqueue("T-1", "alert text")
            outbox.enqueue("T-1", "alert text")
            self.assertEqual(outbox.pending_count(), 1)

            self.assertEqual(outbox.deliver_pending(lambda _message: {"status": "ERROR"}), 0)
            self.assertEqual(outbox.pending_count(), 1)

            self.assertEqual(outbox.deliver_pending(lambda _message: {"status": "SENT", "message_id": 7}), 1)
            self.assertEqual(outbox.pending_count(), 0)


if __name__ == "__main__":
    unittest.main()
