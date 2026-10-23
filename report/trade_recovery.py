
from typing import Any
from datetime import datetime
import math

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

        required = ("trade_id", "status", "symbol", "entry", "option_sl", "option_target", "direction", "entry_time")
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
        direction = str(saved_trade.get("direction", "")).strip().upper()
        if direction not in {"CE", "PE"}:
            raise ValueError(f"Saved trade direction is invalid: {direction!r}.")
        try:
            entry_time = datetime.fromisoformat(str(saved_trade["entry_time"]))
        except (TypeError, ValueError) as exc:
            raise ValueError("Saved trade entry_time must be an ISO timestamp.") from exc
        if entry_time.tzinfo is None:
            raise ValueError("Saved trade entry_time must include a timezone.")
        if saved_trade.get("index_entry") is not None or saved_trade.get("index_sl") is not None:
            try:
                index_entry = float(saved_trade["index_entry"])
                index_sl = float(saved_trade["index_sl"])
                index_distance = index_entry - index_sl if direction == "CE" else index_sl - index_entry
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                raise ValueError("Saved index entry/SL must be numeric and complete.") from exc
            if not math.isfinite(index_entry) or not math.isfinite(index_sl) or index_distance <= 0 or index_distance > 50:
                raise ValueError("Saved trade violates the maximum 50 SENSEX index-point SL rule.")

        if self.trade_manager.has_active_trade():
            raise RuntimeError(
                "Cannot recover: an active trade is already registered."
            )

        self.trade_manager.start_trade(saved_trade)
        return saved_trade