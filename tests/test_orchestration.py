from agent.orchestration.graph import AgentFinding, AgentRole, ForexAgentGraph


def test_risk_rejection_forces_no_trade() -> None:
    graph = ForexAgentGraph()
    state = graph.initialize("AUDUSD", "M15")
    graph.add_finding(
        state,
        AgentFinding(
            role=AgentRole.TECHNICAL,
            summary="bullish momentum",
            evidence=["EMA alignment"],
            confidence=0.8,
        ),
    )
    graph.set_strategy_decision(state, "BUY")
    graph.apply_risk_decision(state, False, "risk limit exceeded")

    assert state.decision == "NO_TRADE"
    assert state.risk_allowed is False
    assert state.metadata["risk_reason"] == "risk limit exceeded"
