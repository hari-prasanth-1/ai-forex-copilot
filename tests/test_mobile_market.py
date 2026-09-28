from unittest.mock import patch

from api.mobile_market import build_mobile_analysis


def _payload():
    values = [1.0 + i * 0.001 for i in range(50)]
    return {
        "chart": {
            "result": [
                {
                    "timestamp": list(range(50)),
                    "indicators": {
                        "quote": [
                            {
                                "open": values,
                                "high": [v + 0.002 for v in values],
                                "low": [v - 0.002 for v in values],
                                "close": [v + 0.001 for v in values],
                                "volume": [100.0] * 50,
                            }
                        ]
                    },
                }
            ]
        }
    }


def test_mobile_analysis_is_read_only():
    with patch("market_data.providers.yahoo_chart.urlopen"):
        with patch(
            "market_data.providers.yahoo_chart.json.load",
            return_value=_payload(),
        ):
            result = build_mobile_analysis("AUDUSD")
    assert result["source"] == "yahoo_chart"
    assert result["symbol"] == "AUDUSD"
    assert result["execution_enabled"] is False
    assert result["candle_count"] == 50
