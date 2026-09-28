"""Deterministic market-structure classification."""
from __future__ import annotations

from collections.abc import Sequence

from market_data.models import Candle


def classify_structure(candles: Sequence[Candle], lookback: int = 5) -> dict[str, object]:
    if lookback < 2:
        raise ValueError("lookback must be at least 2")
    if len(candles) < lookback * 2 + 1:
        return {
            "trend": "UNKNOWN",
            "event": "INSUFFICIENT_DATA",
            "swing_high": None,
            "swing_low": None,
        }

    recent = candles[-lookback:]
    previous = candles[-2 * lookback : -lookback]
    recent_high = max(c.high for c in recent)
    previous_high = max(c.high for c in previous)
    recent_low = min(c.low for c in recent)
    previous_low = min(c.low for c in previous)

    if recent_high > previous_high and recent_low > previous_low:
        trend = "BULLISH"
    elif recent_high < previous_high and recent_low < previous_low:
        trend = "BEARISH"
    else:
        trend = "RANGE"

    last_close = candles[-1].close
    if last_close > previous_high:
        event = "BOS_UP"
    elif last_close < previous_low:
        event = "BOS_DOWN"
    else:
        event = "NONE"

    return {
        "trend": trend,
        "event": event,
        "swing_high": recent_high,
        "swing_low": recent_low,
    }
