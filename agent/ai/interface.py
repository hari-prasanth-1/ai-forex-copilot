"""AI reasoning boundary; provider implementations are intentionally deferred."""
from abc import ABC, abstractmethod

from agent.analysis.models import TradeSetup


class AIReasoner(ABC):
    @abstractmethod
    def explain(self, setup: TradeSetup) -> str:
        raise NotImplementedError


class DisabledAIReasoner(AIReasoner):
    def explain(self, setup: TradeSetup) -> str:
        return "AI reasoning is not configured; deterministic analysis remains authoritative."
