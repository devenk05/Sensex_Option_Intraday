import time
from typing import Any, Callable, Dict, Optional, Tuple

from trade_exit_monitor import TradeExitMonitor


class TradeExitMonitorLoop:
    """
    Repeatedly checks an active trade's exit conditions.
    Dispatches an EXIT signal only once per trade.
    A new trade is eligible for a new exit signal.
    """

    def __init__(
        self,
        get_active_trade: Callable[[], Dict[str, Any]],
        get_current_option_price: Callable[[Dict[str, Any]], float],
        on_exit_signal: Callable[[Dict[str, Any]], None],
        interval_seconds: float = 1.0,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero.")

        self.get_active_trade = get_active_trade
        self.get_current_option_price = get_current_option_price
        self.on_exit_signal = on_exit_signal
        self.interval_seconds = interval_seconds
        self.monitor = TradeExitMonitor()
        self.running = False

        self._last_exit_trade_key: Optional[Tuple[str, ...]] = None

    @staticmethod
    def _get_trade_key(trade: Dict[str, Any]) -> Tuple[str, ...]:
        """Build a stable identity for the active trade."""
        trade_id = trade.get("trade_id")

        if trade_id is not None:
            return ("trade_id", str(trade_id))

        # Fallback identity when trade_id is not available.
        return (
            "fallback",
            str(trade.get("symbol", "")),
            str(trade.get("entry_time", trade.get("timestamp", ""))),
            str(trade.get("entry_price", "")),
        )

    def run_once(self) -> Dict[str, Any]:
        trade = self.get_active_trade()

        if not trade:
            return {
                "status": "NO_ACTIVE_TRADE",
                "reason": "No active trade found.",
            }

        trade_key = self._get_trade_key(trade)

        current_price = self.get_current_option_price(trade)

        result = self.monitor.monitor_trade(
            trade=trade,
            current_option_price=current_price,
        )

        if result.get("status") == "EXIT":
            if trade_key == self._last_exit_trade_key:
                return {
                    **result,
                    "exit_signal_dispatched": False,
                    "reason": "Exit signal already dispatched for this trade.",
                }

            # Mark before callback to prevent repeated dispatch if callback fails.
            self._last_exit_trade_key = trade_key
            self.on_exit_signal(result)

            return {
                **result,
                "exit_signal_dispatched": True,
            }

        return result

    def start(self) -> None:
        self.running = True

        while self.running:
            self.run_once()
            time.sleep(self.interval_seconds)

    def stop(self) -> None:
        self.running = False
