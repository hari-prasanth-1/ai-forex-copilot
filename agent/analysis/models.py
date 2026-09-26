"""Structured trade-signal contracts."""
from dataclasses import dataclass, field
from enum import StrEnum


class Signal(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True)
class TradeSetup:
    symbol: str
    signal: Signal
    timeframe: str
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    evidence: tuple[str, ...] = field(default_factory=tuple)
    invalidation: str | None = None
