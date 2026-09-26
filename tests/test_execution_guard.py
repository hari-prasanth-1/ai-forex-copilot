import pytest

from mt5.bridge.execution import DisabledMT5Execution, ExecutionDisabledError


def test_phase_one_execution_is_disabled():
    adapter = DisabledMT5Execution()
    with pytest.raises(ExecutionDisabledError):
        adapter.submit_demo_order(symbol="AUDUSD")
