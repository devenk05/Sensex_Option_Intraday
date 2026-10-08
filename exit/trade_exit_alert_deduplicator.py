from typing import Any, Dict, Set, Tuple


class TradeExitAlertDeduplicator:
    """Prevents repeated processing of the same exit signal."""

    def __init__(self) -> None:
        self._processed_signal_keys: Set[Tuple[str, ...]] = set()

    def _make_key(self, signal: Dict[str, Any]) -> Tuple[str, ...]:
        trade_id = signal.get("trade_id")

        if trade_id is not None and str(trade_id).strip():
            trade_identity = ("trade_id", str(trade_id))
        else:
            trade_identity = (
                "fallback",
                str(signal.get("symbol", "")),
                str(signal.get("entry_time", signal.get("timestamp", ""))),
                str(signal.get("entry_price", "")),
            )

        return trade_identity + (
            str(signal.get("status", "")),
            str(signal.get("reason", "")),
        )

    def is_duplicate(self, signal: Dict[str, Any]) -> bool:
        if not isinstance(signal, dict):
            raise TypeError("signal must be a dictionary.")

        key = self._make_key(signal)

        if key in self._processed_signal_keys:
            return True

        self._processed_signal_keys.add(key)
        return False

    def reset(self) -> None:
        self._processed_signal_keys.clear()
