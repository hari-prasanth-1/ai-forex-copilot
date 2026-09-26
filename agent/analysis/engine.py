"""Deterministic analysis orchestration contracts."""
from dataclasses import dataclass

from agent.analysis.models import Signal, TradeSetup


@dataclass(frozen=True)
class AnalysisContext:
    symbol: str
    timeframe: str
    indicators: dict[str, float | None]
    evidence: tuple[str, ...] = ()


class TechnicalAnalysisEngine:
    """Builds a transparent setup from already-computed market evidence."""

    def analyze(self, context: AnalysisContext) -> TradeSetup:
        ema20 = context.indicators.get("ema20")
        ema50 = context.indicators.get("ema50")
        rsi_value = context.indicators.get("rsi")
        evidence = list(context.evidence)

        if ema20 is None or ema50 is None or rsi_value is None:
            evidence.append("insufficient_indicator_data")
            return TradeSetup(
                context.symbol,
                Signal.NO_TRADE,
                context.timeframe,
                evidence=tuple(evidence),
            )

        if ema20 > ema50 and rsi_value >= 50:
            evidence.extend(["ema20_above_ema50", "rsi_supports_bullish_bias"])
            return TradeSetup(
                context.symbol,
                Signal.BUY,
                context.timeframe,
                evidence=tuple(evidence),
            )

        if ema20 < ema50 and rsi_value <= 50:
            evidence.extend(["ema20_below_ema50", "rsi_supports_bearish_bias"])
            return TradeSetup(
                context.symbol,
                Signal.SELL,
                context.timeframe,
                evidence=tuple(evidence),
            )

        evidence.append("mixed_indicator_evidence")
        return TradeSetup(
            context.symbol,
            Signal.NO_TRADE,
            context.timeframe,
            evidence=tuple(evidence),
        )
