from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_health_keeps_execution_disabled() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["execution_enabled"] is False


def test_market_contract_defaults_to_m15() -> None:
    response = client.get("/market/AUDUSD")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AUDUSD"
    assert body["timeframe"] == "M15"
    assert body["data_source"] == "mt5_read_only"
    assert body["live_data"] is False


def test_analysis_is_no_trade_until_feed_exists() -> None:
    response = client.get("/analysis/AUDUSD?timeframe=H1")
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "NO_TRADE"
    assert body["execution_enabled"] is False


def test_kill_switch_forces_analysis_only() -> None:
    response = client.post("/mode", json={"mode": "auto_demo"})
    assert response.status_code == 200
    assert response.json()["execution_enabled"] is False

    response = client.post("/kill-switch")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "analysis_only"
    assert body["kill_switch"] is True
    assert body["execution_enabled"] is False


def test_live_paper_endpoint_is_declared() -> None:
    paths = app.openapi()["paths"]
    assert "/paper/live/{symbol}" in paths
