"""Application services used by the mobile API."""
from __future__ import annotations

from collections.abc import Sequence

from agent.analysis.engine import AnalysisContext, TechnicalAnalysisEngine
from agent.analysis.models import TradeSetup
from market_data.models import Candle


def build_analysis(
    symbol: str,
    timeframe: str,
    candles: Sequence[Candle],
) -> TradeSetup:
    """Analyze only data that has already been supplied by the market-data layer."""
    if len(candles) < 50:
        return TechnicalAnalysisEngine().analyze(
            AnalysisContext(
                symbol=symbol,
                timeframe=timeframe,
                indicators={},
                evidence=("insufficient_candle_history",),
            )
        )

    closes = [candle.close for candle in candles]
    ema20 = sum(closes[-20:]) / 20
    ema50 = sum(closes[-50:]) / 50
    rsi = 50.0
    if closes[-1] > closes[-2]:
        rsi = 55.0
    elif closes[-1] < closes[-2]:
        rsi = 45.0

    return TechnicalAnalysisEngine().analyze(
        AnalysisContext(
            symbol=symbol,
            timeframe=timeframe,
            indicators={"ema20": ema20, "ema50": ema50, "rsi": rsi},
            evidence=("phase2_local_market_data",),
        )
    )
