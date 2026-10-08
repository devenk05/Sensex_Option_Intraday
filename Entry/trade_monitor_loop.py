
import time
from typing import Any, Callable

from trade_monitor import TradeMonitor


class TradeMonitorLoop:
    """Periodically check active trade status."""

    def __init__(
        self,
        monitor: TradeMonitor,
        on_update: Callable[[dict[str, Any]], None] | None = None,
        interval_seconds: int = 1,
    ) -> None:
        if interval_seconds < 1:
            raise ValueError("Interval must be at least 1 second.")

        self.monitor = monitor
        self.on_update = on_update
        self.interval_seconds = interval_seconds
        self._running = False

    def run_forever(self) -> None:
        """Continuously check the active trade status."""

        self._running = True

        while self._running:
            try:
                status = self.monitor.get_status()

                if self.on_update is not None:
                    self.on_update(status)

            except Exception as exc:
                print(f"Trade monitor error: {exc}")

            time.sleep(self.interval_seconds)

    def stop(self) -> None:
        """Request the loop to stop."""
        self._running = False