from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from market_data.models import Candle, Timeframe
from mt5.bridge.market_data import (
    DisabledMT5MarketData,
    InMemoryMarketData,
    MarketRequest,
    candle_from_mt5_row,
)


def sample_candles() -> list[Candle]:
    return [
        Candle(
            timestamp=datetime(2026, 9, 26, 10, index, tzinfo=timezone.utc),
            open=0.7000 + index * 0.0001,
            high=0.7010 + index * 0.0001,
            low=0.6990 + index * 0.0001,
            close=0.7005 + index * 0.0001,
            volume=100 + index,
        )
        for index in range(3)
    ]


def test_market_request_validates_symbol_and_limit() -> None:
    assert MarketRequest("AUDUSD", Timeframe.M15, 50).limit == 50
    with pytest.raises(ValueError, match="symbol"):
        MarketRequest(" ", Timeframe.M15)
    with pytest.raises(ValueError, match="between 1 and 5000"):
        MarketRequest("AUDUSD", Timeframe.M15, 0)


def test_in_memory_adapter_returns_requested_tail() -> None:
    adapter = InMemoryMarketData(sample_candles())
    candles = adapter.get_candles(MarketRequest("AUDUSD", Timeframe.M15, 2))
    assert len(candles) == 2
    assert candles[0].close < candles[1].close


def test_disabled_mt5_adapter_never_returns_live_data() -> None:
    with pytest.raises(RuntimeError, match="not connected"):
        DisabledMT5MarketData().get_candles(MarketRequest("AUDUSD", Timeframe.M15))


def test_mt5_row_is_normalized_to_internal_candle() -> None:
    row = SimpleNamespace(
        time=1790416800,
        open=0.7000,
        high=0.7020,
        low=0.6990,
        close=0.7010,
        tick_volume=123,
    )
    candle = candle_from_mt5_row(row)
    assert candle.timestamp.tzinfo == timezone.utc
    assert candle.close == pytest.approx(0.7010)
    assert candle.volume == 123


def test_mt5_adapter_initializes_and_reads_bars() -> None:
    rows = [
        SimpleNamespace(
            time=1790416800,
            open=0.7000,
            high=0.7020,
            low=0.6990,
            close=0.7010,
            tick_volume=123,
        )
    ]

    class FakeMT5:
        TIMEFRAME_M15 = "M15"

        def __init__(self) -> None:
            self.initialized = False
            self.shutdown_called = False

        def initialize(self) -> bool:
            self.initialized = True
            return True

        def copy_rates_from_pos(self, symbol, timeframe, start, count):
            assert self.initialized is True
            assert symbol == "AUDUSD"
            assert timeframe == "M15"
            assert start == 0
            assert count == 50
            return rows

        def shutdown(self) -> None:
            self.shutdown_called = True

    from mt5.bridge.market_data import MetaTrader5MarketData

    fake = FakeMT5()
    adapter = MetaTrader5MarketData(mt5_module=fake)
    assert adapter.connected is True
    candles = adapter.get_candles(MarketRequest("AUDUSD", Timeframe.M15, 50))
    assert len(candles) == 1
    assert candles[0].close == pytest.approx(0.7010)
    adapter.shutdown()
    assert fake.shutdown_called is True
