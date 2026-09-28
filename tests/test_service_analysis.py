from datetime import datetime, timedelta, timezone

from api.services import build_analysis
from market_data.models import Candle


def test_service_uses_deterministic_indicator_pipeline() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles = [
        Candle(
            start + timedelta(minutes=i),
            1.0 + i * 0.001,
            1.002 + i * 0.001,
            0.998 + i * 0.001,
            1.001 + i * 0.001,
            100 + i,
        )
        for i in range(60)
    ]
    setup = build_analysis("AUDUSD", "M15", candles)
    assert setup.signal.value == "BUY"
    assert "phase2_deterministic_indicators" in setup.evidence
