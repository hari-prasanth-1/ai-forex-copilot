"""Core market data models."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Timeframe(StrEnum):
    M5 = "M5"
    M15 = "M15"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.high < max(self.open, self.close):
            raise ValueError("High must be at least open and close")
        if self.low > min(self.open, self.close):
            raise ValueError("Low must be at most open and close")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
