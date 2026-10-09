import pytest

from mt5.bridge.demo_execution import ExecutionRejected, submit_demo_order


def test_demo_executor_rejects_invalid_side_before_connecting() -> None:
    with pytest.raises(ExecutionRejected, match="side must be BUY or SELL"):
        submit_demo_order(
            symbol="AUDUSD",
            side="HOLD",
            volume=0.01,
            stop_loss=0.69,
            take_profit=0.71,
            orders_today=0,
        )


def test_demo_executor_rejects_volume_above_hard_cap_before_connecting() -> None:
    with pytest.raises(ExecutionRejected, match="at most 0.01"):
        submit_demo_order(
            symbol="AUDUSD",
            side="BUY",
            volume=0.02,
            stop_loss=0.69,
            take_profit=0.71,
            orders_today=0,
        )


def test_demo_executor_requires_stop_and_target() -> None:
    with pytest.raises(ExecutionRejected, match="Stop-loss and take-profit"):
        submit_demo_order(
            symbol="AUDUSD",
            side="BUY",
            volume=0.01,
            stop_loss=0,
            take_profit=0.71,
            orders_today=0,
        )


def test_demo_executor_blocks_after_daily_order_limit() -> None:
    with pytest.raises(ExecutionRejected, match="Daily order limit"):
        submit_demo_order(
            symbol="AUDUSD",
            side="BUY",
            volume=0.01,
            stop_loss=0.69,
            take_profit=0.71,
            orders_today=3,
        )
