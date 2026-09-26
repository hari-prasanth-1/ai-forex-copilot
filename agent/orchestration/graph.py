from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentRole(str, Enum):
    TECHNICAL = "technical"
    STRUCTURE = "structure"
    CONTEXT = "context"
    STRATEGY = "strategy"
    RISK = "risk"
    EXPLANATION = "explanation"


@dataclass
class AgentFinding:
    role: AgentRole
    summary: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class AgentState:
    symbol: str
    timeframe: str
    findings: list[AgentFinding] = field(default_factory=list)
    decision: str = "NO_TRADE"
    risk_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class ForexAgentGraph:
    """Deterministic orchestration shell for specialized analysis agents.

    Phase 1 deliberately keeps execution outside the graph. LLM providers can
    later implement individual roles without gaining authority over risk rules.
    """

    def __init__(self, roles: tuple[AgentRole, ...] | None = None) -> None:
        self.roles = roles or (
            AgentRole.TECHNICAL,
            AgentRole.STRUCTURE,
            AgentRole.CONTEXT,
            AgentRole.STRATEGY,
            AgentRole.RISK,
            AgentRole.EXPLANATION,
        )

    def initialize(self, symbol: str, timeframe: str) -> AgentState:
        if not symbol or not timeframe:
            raise ValueError("symbol and timeframe are required")
        return AgentState(symbol=symbol, timeframe=timeframe)

    def add_finding(self, state: AgentState, finding: AgentFinding) -> AgentState:
        if finding.role not in self.roles:
            raise ValueError(f"unsupported agent role: {finding.role}")
        if not 0.0 <= finding.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        state.findings.append(finding)
        return state

    def set_strategy_decision(self, state: AgentState, decision: str) -> AgentState:
        normalized = decision.upper()
        if normalized not in {"BUY", "SELL", "NO_TRADE"}:
            raise ValueError("decision must be BUY, SELL, or NO_TRADE")
        state.decision = normalized
        return state

    def apply_risk_decision(self, state: AgentState, allowed: bool, reason: str) -> AgentState:
        state.risk_allowed = allowed
        state.metadata["risk_reason"] = reason
        if not allowed:
            state.decision = "NO_TRADE"
        return state
