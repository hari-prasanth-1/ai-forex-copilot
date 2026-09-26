from agent.analysis.engine import AnalysisContext, TechnicalAnalysisEngine
from agent.analysis.models import Signal


def test_bullish_evidence_returns_buy():
    setup = TechnicalAnalysisEngine().analyze(
        AnalysisContext("AUDUSD", "M15", {"ema20": 0.67, "ema50": 0.66, "rsi": 55})
    )
    assert setup.signal == Signal.BUY


def test_mixed_evidence_returns_no_trade():
    setup = TechnicalAnalysisEngine().analyze(
        AnalysisContext("AUDUSD", "M15", {"ema20": 0.67, "ema50": 0.66, "rsi": 45})
    )
    assert setup.signal == Signal.NO_TRADE
