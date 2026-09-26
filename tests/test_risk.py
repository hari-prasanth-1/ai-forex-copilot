from agent.risk.engine import evaluate_trade


def test_risk_rejects_low_rr():
    decision = evaluate_trade(
        balance=1000,
        risk_pct=1,
        entry=100,
        stop_loss=99,
        take_profit=101,
        min_risk_reward=2,
    )
    assert not decision.allowed
    assert "minimum_risk_reward_not_met" in decision.reasons


def test_risk_accepts_valid_rr():
    decision = evaluate_trade(
        balance=1000,
        risk_pct=1,
        entry=100,
        stop_loss=99,
        take_profit=102,
        min_risk_reward=2,
    )
    assert decision.allowed
    assert decision.risk_amount == 10
    assert decision.risk_reward == 2
