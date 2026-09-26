"""Read-only MT5 market-data boundary."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, Sequence

from market_data.models import Candle, Timeframe


@dataclass(frozen=True)
class MarketRequest:
    symbol: str
    timeframe: Timeframe
    limit: int = 200

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if not 1 <= self.limit <= 5000:
            raise ValueError("limit must be between 1 and 5000")


class MarketDataPort(Protocol):
    """Provider-neutral, read-only market-data contract."""

    def get_candles(self, request: MarketRequest) -> Sequence[Candle]:
        ...


class DisabledMT5MarketData:
    """Explicit boundary until a real MT5 terminal bridge is connected."""

    def get_candles(self, request: MarketRequest) -> Sequence[Candle]:
        raise RuntimeError(
            "MT5 market-data bridge is not connected; no live data available"
        )


class InMemoryMarketData:
    """Deterministic adapter for tests and local development."""

    def __init__(self, candles: Sequence[Candle]) -> None:
        self._candles = tuple(candles)

    def get_candles(self, request: MarketRequest) -> Sequence[Candle]:
        return self._candles[-request.limit :]


def candle_from_mt5_row(row: object) -> Candle:
    """Normalize an MT5-like row into the internal Candle model."""
    timestamp = datetime.fromtimestamp(float(row.time), tz=timezone.utc)
    return Candle(
        timestamp=timestamp,
        open=float(row.open),
        high=float(row.high),
        low=float(row.low),
        close=float(row.close),
        volume=float(row.tick_volume),
    )
