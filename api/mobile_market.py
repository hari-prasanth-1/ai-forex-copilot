from __future__ import annotations

from api.services import build_analysis
from market_data.models import Timeframe
from market_data.providers.yahoo_chart import YahooChartMarketData


def build_mobile_analysis(
    symbol: str = "AUDUSD",
    timeframe: Timeframe = Timeframe.M15,
    limit: int = 200,
):
    candles = YahooChartMarketData().get_candles(symbol, timeframe, limit)
    analysis = build_analysis(symbol, timeframe, candles)
    return {
        "source": "yahoo_chart",
        "symbol": symbol,
        "timeframe": timeframe.value,
        "candle_count": len(candles),
        "latest_close": candles[-1].close,
        "decision": analysis.decision.value,
        "evidence": analysis.evidence,
        "execution_enabled": False,
    }
