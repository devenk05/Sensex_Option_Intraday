from typing import Any, Dict, Optional, Tuple


class TradeExitAlertDeduplicator:
    """Prevents repeated processing of the same exit signal."""

    def __init__(self) -> None:
        self._last_signal_key: Optional[Tuple[str, str, str]] = None

    def is_duplicate(self, signal: Dict[str, Any]) -> bool:
        if not isinstance(signal, dict):
            raise TypeError("signal must be a dictionary.")

        key = (
            str(signal.get("trade_id", "")),
            str(signal.get("status", "")),
            str(signal.get("reason", "")),
        )

        if key == self._last_signal_key:
            return True

        self._last_signal_key = key
        return False

    def reset(self) -> None:
        self._last_signal_key = None
