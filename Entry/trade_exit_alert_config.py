from dataclasses import dataclass


@dataclass(frozen=True)
class TradeExitAlertConfig:
    """Configuration for trade exit alerts."""

    enabled: bool = True
    log_enabled: bool = True
    telegram_enabled: bool = True
    retry_count: int = 3
    retry_delay_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.retry_count < 0:
            raise ValueError("retry_count cannot be negative.")

        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative.")
