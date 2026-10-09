import pytest

from agent.orchestration.auto_demo import AutoDemoBot


def test_auto_demo_is_stopped_by_default() -> None:
    status = AutoDemoBot().status()
    assert status["running"] is False
    assert status["execution_enabled"] is False
    assert status["last_decision"] == "WAIT"


def test_auto_demo_requires_exact_confirmation() -> None:
    with pytest.raises(ValueError, match="Exact confirmation"):
        AutoDemoBot().start("start")


def test_auto_demo_requires_explicit_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOREX_COPILOT_ENABLE_DEMO_ORDERS", "false")
    monkeypatch.setenv("FOREX_COPILOT_ENABLE_AUTO_DEMO", "false")
    with pytest.raises(ValueError, match="FOREX_COPILOT_ENABLE_DEMO_ORDERS"):
        AutoDemoBot().start("START DEMO AUTO BOT")


def test_auto_demo_requires_ai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOREX_COPILOT_ENABLE_DEMO_ORDERS", "true")
    monkeypatch.setenv("FOREX_COPILOT_ENABLE_AUTO_DEMO", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        AutoDemoBot().start("START DEMO AUTO BOT")


def test_auto_demo_rejects_invalid_timeframe_before_starting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOREX_COPILOT_ENABLE_DEMO_ORDERS", "true")
    monkeypatch.setenv("FOREX_COPILOT_ENABLE_AUTO_DEMO", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    with pytest.raises(ValueError, match="Supported timeframes"):
        AutoDemoBot().start("START DEMO AUTO BOT", "AUDUSD", "TICK")
