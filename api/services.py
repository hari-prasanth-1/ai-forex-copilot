"""Application services used by the mobile API."""
from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from agent.analysis.engine import AnalysisContext, TechnicalAnalysisEngine
from agent.analysis.models import TradeSetup
from market_data.indicators import atr, ema, macd, rsi
from market_data.models import Candle
from market_data.structure import classify_structure


def build_analysis(symbol: str, timeframe: str, candles: Sequence[Candle]) -> TradeSetup:
    """Run deterministic indicators + structure; never places an order."""
    if len(candles) < 50:
        return TechnicalAnalysisEngine().analyze(
            AnalysisContext(
                symbol=symbol,
                timeframe=timeframe,
                indicators={},
                evidence=("insufficient_candle_history",),
            )
        )

    closes = pd.Series([c.close for c in candles], dtype="float64")
    highs = pd.Series([c.high for c in candles], dtype="float64")
    lows = pd.Series([c.low for c in candles], dtype="float64")
    ema20 = float(ema(closes, 20).iloc[-1])
    ema50 = float(ema(closes, 50).iloc[-1])
    rsi14 = rsi(closes, 14).iloc[-1]
    macd_frame = macd(closes)
    atr14 = atr(highs, lows, closes).iloc[-1]
    structure = classify_structure(candles)

    evidence = [
        "phase2_deterministic_indicators",
        f"structure_{str(structure['trend']).lower()}",
        f"structure_event_{str(structure['event']).lower()}",
    ]
    if pd.notna(macd_frame["histogram"].iloc[-1]):
        evidence.append("macd_available")
    if pd.notna(atr14):
        evidence.append("atr_available")

    return TechnicalAnalysisEngine().analyze(
        AnalysisContext(
            symbol=symbol,
            timeframe=timeframe,
            indicators={"ema20": ema20, "ema50": ema50, "rsi": float(rsi14)},
            evidence=tuple(evidence),
        )
    )
