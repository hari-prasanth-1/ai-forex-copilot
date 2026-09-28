from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

from market_data.models import Candle, Timeframe


class YahooChartMarketData:
    """Read-only market-data adapter for mobile development."""

    _INTERVALS = {
        Timeframe.M5: "5m",
        Timeframe.M15: "15m",
        Timeframe.H1: "1h",
        Timeframe.H4: "1h",
    }

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def get_candles(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.M15,
        limit: int = 200,
    ) -> list[Candle]:
        if limit < 50 or limit > 5000:
            raise ValueError("limit must be between 50 and 5000")
        yahoo_symbol = quote(self._to_yahoo_symbol(symbol), safe="")
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{yahoo_symbol}?interval={self._INTERVALS[timeframe]}&range=1mo&events=history"
        )
        request = Request(url, headers={"User-Agent": "ai-forex-copilot/0.1"})
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.load(response)
        result = payload["chart"]["result"][0]
        timestamps = result.get("timestamp") or []
        quote_data = result["indicators"]["quote"][0]
        candles = []
        for index, timestamp in enumerate(timestamps):
            values = {
                key: quote_data.get(key, [None] * len(timestamps))[index]
                for key in ("open", "high", "low", "close", "volume")
            }
            if any(value is None for value in values.values()):
                continue
            candles.append(
                Candle(
                    timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
                    open=float(values["open"]),
                    high=float(values["high"]),
                    low=float(values["low"]),
                    close=float(values["close"]),
                    volume=float(values["volume"]),
                )
            )
        if not candles:
            raise RuntimeError(f"No market data returned for {symbol}")
        return candles[-limit:]

    @staticmethod
    def _to_yahoo_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        return "AUDUSD=X" if normalized == "AUDUSD" else normalized
