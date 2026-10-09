from datetime import datetime, timedelta, timezone

from api.chart_data import build_chart_payload
from market_data.models import Candle, Timeframe


def test_chart_payload_includes_candles_indicators_and_read_only_guard() -> None:
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    candles = []
    for index in range(240):
        close = 0.6500 + index * 0.00008
        candles.append(
            Candle(
                timestamp=start + timedelta(minutes=15 * index),
                open=close - 0.00003,
                high=close + 0.00012,
                low=close - 0.00012,
                close=close,
                volume=100 + index,
            )
        )

    payload = build_chart_payload("AUDUSD", Timeframe.M15, candles)

    assert payload["symbol"] == "AUDUSD"
    assert payload["timeframe"] == "M15"
    assert payload["source"] == "mt5_terminal"
    assert payload["execution_enabled"] is False
    assert len(payload["candles"]) == 240
    latest = payload["candles"][-1]
    assert latest["ema20"] is not None
    assert latest["ema50"] is not None
    assert latest["ema200"] is not None
    assert latest["rsi14"] is not None
    assert latest["macd"] is not None
    assert latest["macd_signal"] is not None
    assert latest["macd_histogram"] is not None
    assert latest["atr14"] is not None
    assert latest["volume"] == 339
