from datetime import datetime, timedelta, timezone

from market_data.models import Candle
from market_data.structure import classify_structure


def test_structure_detects_bullish_trend_and_break() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    values = [1.0, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09]
    candles = [
        Candle(start + timedelta(minutes=i), value, value + .002, value - .002, value + .001, 100)
        for i, value in enumerate(values)
    ]
    result = classify_structure(candles, lookback=3)
    assert result["trend"] == "BULLISH"
    assert result["event"] == "BOS_UP"
