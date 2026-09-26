"""Deterministic risk calculations. No broker/order side effects."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    risk_amount: float
    position_size: float
    risk_reward: float
    reasons: tuple[str, ...] = ()


def position_size(balance: float, risk_pct: float, stop_distance: float, value_per_unit: float = 1.0) -> float:
    if balance <= 0 or risk_pct <= 0 or stop_distance <= 0 or value_per_unit <= 0:
        raise ValueError("Balance, risk percentage, stop distance and unit value must be positive")
    risk_amount = balance * risk_pct / 100
    return risk_amount / (stop_distance * value_per_unit)


def evaluate_trade(
    *,
    balance: float,
    risk_pct: float,
    entry: float,
    stop_loss: float,
    take_profit: float,
    min_risk_reward: float = 2.0,
) -> RiskDecision:
    if balance <= 0:
        return RiskDecision(False, 0.0, 0.0, 0.0, ("invalid_balance",))
    if risk_pct <= 0:
        return RiskDecision(False, 0.0, 0.0, 0.0, ("invalid_risk_pct",))
    if min_risk_reward <= 0:
        return RiskDecision(False, 0.0, 0.0, 0.0, ("invalid_min_risk_reward",))

    risk_distance = abs(entry - stop_loss)
    reward_distance = abs(take_profit - entry)
    if risk_distance == 0:
        return RiskDecision(False, 0.0, 0.0, 0.0, ("zero_stop_distance",))

    rr = reward_distance / risk_distance
    risk_amount = balance * risk_pct / 100
    size = position_size(balance, risk_pct, risk_distance)

    if rr < min_risk_reward:
        return RiskDecision(False, risk_amount, size, rr, ("minimum_risk_reward_not_met",))
    return RiskDecision(True, risk_amount, size, rr)
