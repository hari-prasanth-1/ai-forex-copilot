"""Backtesting contracts with explicit no-lookahead intent."""
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class Strategy(Protocol):
    def on_candle(self, candles: Sequence[Candle]) -> str:
        """Return a signal using only candles available up to this point."""
        ...


@dataclass(frozen=True)
class BacktestResult:
    trades: int
    net_pnl: float
    max_drawdown: float


class BacktestEngine:
    def run(self, candles: Sequence[Candle], strategy: Strategy) -> BacktestResult:
        for index in range(len(candles)):
            strategy.on_candle(candles[: index + 1])
        return BacktestResult(trades=0, net_pnl=0.0, max_drawdown=0.0)
