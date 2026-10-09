"""Read-only MT5 market-data boundary and optional terminal adapter."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, Sequence

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
    def get_candles(self, request: MarketRequest) -> Sequence[Candle]:
        ...


class DisabledMT5MarketData:
    """Safe default: no terminal connection and no live data."""

    def get_candles(self, request: MarketRequest) -> Sequence[Candle]:
        raise RuntimeError("MT5 market-data bridge is not connected; no live data available")


class InMemoryMarketData:
    """Deterministic adapter for tests and local development."""

    def __init__(self, candles: Sequence[Candle]) -> None:
        self._candles = tuple(candles)

    def get_candles(self, request: MarketRequest) -> Sequence[Candle]:
        return self._candles[-request.limit:]


class MetaTrader5MarketData:
    """Read-only adapter for a locally running MetaTrader 5 terminal.

    The dependency is imported only when this adapter is instantiated, so CI and
    environments without the MT5 package remain safe and importable.
    """

    _TIMEFRAMES = {
        Timeframe.M5: "TIMEFRAME_M5",
        Timeframe.M15: "TIMEFRAME_M15",
        Timeframe.H1: "TIMEFRAME_H1",
        Timeframe.H4: "TIMEFRAME_H4",
    }

    def __init__(self, mt5_module: Any | None = None, initialize: bool = True) -> None:
        if mt5_module is None:
            try:
                import MetaTrader5 as mt5_module  # type: ignore[import-not-found]
            except ImportError as exc:
                raise RuntimeError(
                    "MetaTrader5 Python package is required for live read-only data"
                ) from exc
        self._mt5 = mt5_module
        self._initialized = False
        if initialize:
            self.connect()

    def connect(self) -> None:
        """Connect the Python API to the already-installed MT5 terminal."""
        initialize = getattr(self._mt5, "initialize", None)
        if initialize is None:
            raise RuntimeError("MetaTrader5 module does not expose initialize()")
        if not initialize():
            error = getattr(self._mt5, "last_error", lambda: "unknown MT5 error")()
            raise RuntimeError(f"MT5 terminal initialization failed: {error}")
        self._initialized = True

    @property
    def connected(self) -> bool:
        return self._initialized

    def get_candles(self, request: MarketRequest) -> Sequence[Candle]:
        if not self._initialized:
            raise RuntimeError("MT5 terminal is not initialized")
        timeframe_name = self._TIMEFRAMES[request.timeframe]
        timeframe = getattr(self._mt5, timeframe_name)
        rows = self._mt5.copy_rates_from_pos(request.symbol.upper(), timeframe, 0, request.limit)
        if rows is None:
            error = getattr(self._mt5, "last_error", lambda: "unknown MT5 error")()
            raise RuntimeError(f"MT5 market-data request failed: {error}")
        return tuple(candle_from_mt5_row(row) for row in rows)

    def shutdown(self) -> None:
        """Close the Python API connection without placing any trade."""
        shutdown = getattr(self._mt5, "shutdown", None)
        if shutdown is not None and self._initialized:
            shutdown()
        self._initialized = False


def _row_value(row: object, field: str) -> Any:
    """Read a field from MT5's NumPy structured scalars or attribute-based test rows."""
    try:
        return row[field]  # type: ignore[index]
    except (TypeError, KeyError, IndexError):
        try:
            return getattr(row, field)
        except AttributeError as exc:
            raise ValueError(f"MT5 candle row is missing field {field!r}") from exc


def candle_from_mt5_row(row: object) -> Candle:
    timestamp = datetime.fromtimestamp(float(_row_value(row, "time")), tz=timezone.utc)
    return Candle(
        timestamp=timestamp,
        open=float(_row_value(row, "open")),
        high=float(_row_value(row, "high")),
        low=float(_row_value(row, "low")),
        close=float(_row_value(row, "close")),
        volume=float(_row_value(row, "tick_volume")),
    )
