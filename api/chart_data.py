"""Chart-ready OHLCV and indicator payloads from the read-only MT5 feed."""
from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd

from market_data.indicators import atr, ema, macd, rsi
from market_data.models import Candle, Timeframe
from market_data.structure import classify_structure
from mt5.bridge.market_data import MarketRequest, MetaTrader5MarketData


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def build_chart_payload(symbol: str, timeframe: Timeframe, candles: list[Candle]) -> dict[str, Any]:
    """Calculate display indicators; signals are informational and never execute orders."""
    if not candles:
        raise ValueError("No candles available for chart")
    candles = sorted(candles, key=lambda candle: candle.timestamp)
    closes = pd.Series([c.close for c in candles], dtype="float64")
    highs = pd.Series([c.high for c in candles], dtype="float64")
    lows = pd.Series([c.low for c in candles], dtype="float64")
    ema20, ema50, ema200 = ema(closes, 20), ema(closes, 50), ema(closes, 200)
    rsi14 = rsi(closes, 14)
    macd_frame = macd(closes)
    atr14 = atr(highs, lows, closes, 14)
    structure = classify_structure(candles)

    rows: list[dict[str, Any]] = []
    previous_buy = False
    previous_sell = False
    for index, candle in enumerate(candles):
        e20, e50 = _number(ema20.iloc[index]), _number(ema50.iloc[index])
        rv = _number(rsi14.iloc[index])
        hist = _number(macd_frame["histogram"].iloc[index])
        signal = None
        buy_setup = (
            index > 0
            and e20 is not None
            and e50 is not None
            and rv is not None
            and hist is not None
            and e20 > e50 and rv >= 50 and rv < 70 and hist > 0
            and _number(ema20.iloc[index - 1]) is not None
            and _number(ema50.iloc[index - 1]) is not None
            and _number(ema20.iloc[index - 1]) <= _number(ema50.iloc[index - 1])
        )
        sell_setup = (
            index > 0 and e20 is not None and e50 is not None and rv is not None and hist is not None
            and e20 < e50 and rv <= 50 and rv > 30 and hist < 0
            and _number(ema20.iloc[index - 1]) is not None
            and _number(ema50.iloc[index - 1]) is not None
            and _number(ema20.iloc[index - 1]) >= _number(ema50.iloc[index - 1])
        )
        if buy_setup and not previous_buy:
            signal = "BUY"
        elif sell_setup and not previous_sell:
            signal = "SELL"
        previous_buy, previous_sell = bool(buy_setup), bool(sell_setup)
        rows.append({
            "time": int(candle.timestamp.timestamp()),
            "timestamp": candle.timestamp.isoformat(),
            "open": candle.open, "high": candle.high, "low": candle.low,
            "close": candle.close, "volume": candle.volume,
            "ema20": e20, "ema50": e50, "ema200": _number(ema200.iloc[index]),
            "rsi14": rv, "macd": _number(macd_frame["macd"].iloc[index]),
            "macd_signal": _number(macd_frame["signal"].iloc[index]),
            "macd_histogram": hist, "atr14": _number(atr14.iloc[index]),
            "signal": signal,
        })

    last = rows[-1]
    return {
        "symbol": symbol.upper(), "timeframe": timeframe.value,
        "source": "mt5_terminal", "candles": rows,
        "trend": str(structure["trend"]),
        "structure_event": str(structure["event"]),
        "swing_high": structure["swing_high"], "swing_low": structure["swing_low"],
        "latest": {
            "close": last["close"], "ema20": last["ema20"], "ema50": last["ema50"],
            "ema200": last["ema200"], "rsi14": last["rsi14"],
            "macd": last["macd"], "macd_signal": last["macd_signal"],
            "macd_histogram": last["macd_histogram"], "atr14": last["atr14"],
            "volume": last["volume"],
        },
        "signals_note": (
            "Historical EMA20/EMA50 crossover with RSI and MACD confluence; "
            "informational only."
        ),
        "execution_enabled": False,
    }


def load_mt5_chart(symbol: str, timeframe: Timeframe, limit: int = 200) -> dict[str, Any]:
    if not symbol.strip() or not symbol.replace(".", "").isalnum():
        raise ValueError("Invalid symbol")
    if not 50 <= limit <= 5000:
        raise ValueError("limit must be between 50 and 5000")
    adapter = MetaTrader5MarketData()
    try:
        request = MarketRequest(
            symbol=symbol.upper(), timeframe=timeframe, limit=limit
        )
        candles = list(adapter.get_candles(request))
        return build_chart_payload(symbol, timeframe, candles)
    finally:
        adapter.shutdown()
