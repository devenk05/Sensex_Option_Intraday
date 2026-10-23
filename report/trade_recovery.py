
from typing import Any

from active_trade_manager import ActiveTradeManager
from trade_state_storage import TradeStateStorage


class TradeRecovery:
    """Restore a saved active trade after application restart."""

    def __init__(
        self,
        trade_manager: ActiveTradeManager,
        storage: TradeStateStorage,
    ) -> None:
        self.trade_manager = trade_manager
        self.storage = storage

    def recover(self) -> dict[str, Any] | None:
        """Load saved state and register it with the trade manager."""

        saved_trade = self.storage.load()

        if saved_trade is None:
            return None

        required = ("trade_id", "status", "symbol", "entry", "option_sl", "option_target", "direction")
        missing = [key for key in required if saved_trade.get(key) is None]
        if missing:
            raise ValueError(f"Saved trade state is missing required fields: {missing}")
        status = str(saved_trade.get("status", "")).strip().upper()
        if status != "ACTIVE":
            raise ValueError(f"Saved trade state is not ACTIVE (status={status!r}); refusing recovery.")
        try:
            import math
            numeric = [float(saved_trade[key]) for key in ("entry", "option_sl", "option_target")]
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Saved trade entry/SL/target must be numeric.") from exc
        if not all(math.isfinite(value) and value > 0 for value in numeric):
            raise ValueError("Saved trade entry/SL/target must be finite positive numbers.")
        if numeric[1] >= numeric[2]:
            raise ValueError("Saved BUY-option SL must be below target.")

        if self.trade_manager.has_active_trade():
            raise RuntimeError(
                "Cannot recover: an active trade is already registered."
            )

        self.trade_manager.start_trade(saved_trade)
        return saved_trade