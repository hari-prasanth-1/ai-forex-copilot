from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from api.app import app


def test_post_analysis_accepts_candles() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles = []
    for i in range(60):
        close = 1.0 + i * 0.001
        candles.append({
            "timestamp": (start + timedelta(minutes=i)).isoformat(),
            "open": close - 0.0005,
            "high": close + 0.001,
            "low": close - 0.001,
            "close": close,
            "volume": 100 + i,
        })
    response = TestClient(app).post(
        "/analysis",
        json={"symbol": "AUDUSD", "timeframe": "M15", "candles": candles},
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "BUY"
    assert response.json()["execution_enabled"] is False
