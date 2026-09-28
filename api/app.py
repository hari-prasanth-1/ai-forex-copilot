"""Mobile-ready API boundary for the Forex Copilot."""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import FastAPI, HTTPException, Query\nfrom fastapi.responses import FileResponse\nfrom fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from market_data.models import Candle, Timeframe\nfrom api.services import build_analysis
from mt5.bridge.market_data import MarketRequest, MetaTrader5MarketData\nfrom datetime import datetime


class TradingMode(StrEnum):
    ANALYSIS_ONLY = "analysis_only"
    ASSISTED_DEMO = "assisted_demo"
    AUTO_DEMO = "auto_demo"


class ModeRequest(BaseModel):
    mode: TradingMode


class CandleRequest(BaseModel):\n    timestamp: datetime\n    open: float\n    high: float\n    low: float\n    close: float\n    volume: float = Field(ge=0)\n\n\nclass CandleAnalysisRequest(BaseModel):\n    symbol: str = Field(min_length=1, max_length=12)\n    timeframe: Timeframe = Timeframe.M15\n    candles: list[CandleRequest] = Field(min_length=1, max_length=5000)\n\n\nclass AnalysisResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    decision: str = "NO_TRADE"
    execution_enabled: bool = False
    message: str


class RiskResponse(BaseModel):
    allowed: bool = False
    reason: str
    execution_enabled: bool = False


class LivePaperResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    candles: int
    decision: str
    latest_close: float | None = None
    evidence: list[str] = Field(default_factory=list)
    execution_enabled: bool = False


class SafetyState(BaseModel):
    mode: TradingMode = TradingMode.ANALYSIS_ONLY
    kill_switch: bool = True
    execution_enabled: bool = False


app = FastAPI(title="AI Forex Copilot API", version="0.3.0")\napp.mount("/static", StaticFiles(directory="api/static"), name="static")
_state = SafetyState()\n\n\n@app.get("/", include_in_schema=False)\ndef root() -> FileResponse:\n    return FileResponse("api/static/index.html")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "ai-forex-copilot", "execution_enabled": False}


@app.get("/market/{symbol}")
def market(
    symbol: str,
    timeframe: Timeframe = Query(default=Timeframe.M15),
) -> dict[str, Any]:
    normalized = symbol.upper()
    if not normalized.isalnum():
        raise HTTPException(status_code=400, detail="invalid symbol")
    return {
        "symbol": normalized,
        "timeframe": timeframe,
        "data_source": "mt5_read_only",
        "live_data": False,
        "message": "MT5 terminal bridge is not connected",
    }


@app.get("/analysis/{symbol}", response_model=AnalysisResponse)
def analysis(
    symbol: str,
    timeframe: Timeframe = Query(default=Timeframe.M15),
) -> AnalysisResponse:
    return AnalysisResponse(
        symbol=symbol.upper(),
        timeframe=timeframe,
        message="Analysis requires an available MT5 market-data feed",
    )


@app.post("/analysis", response_model=AnalysisResponse)\ndef analysis_from_candles(request: CandleAnalysisRequest) -> AnalysisResponse:\n    candles = [Candle(c.timestamp, c.open, c.high, c.low, c.close, c.volume) for c in request.candles]\n    setup = build_analysis(request.symbol.upper(), request.timeframe.value, candles)\n    return AnalysisResponse(\n        symbol=setup.symbol, timeframe=request.timeframe, decision=setup.signal.value,\n        message="; ".join(setup.evidence),\n    )\n\n\n@app.get("/risk", response_model=RiskResponse)
def risk() -> RiskResponse:
    return RiskResponse(reason="No trade approved; execution is disabled")


@app.get("/mode", response_model=SafetyState)
def mode() -> SafetyState:
    return _state


@app.post("/mode", response_model=SafetyState)
def set_mode(request: ModeRequest) -> SafetyState:
    # Mode changes never enable live execution. Kill switch remains authoritative.
    _state.mode = request.mode
    _state.execution_enabled = False
    return _state


@app.post("/kill-switch", response_model=SafetyState)
def kill_switch() -> SafetyState:
    _state.kill_switch = True
    _state.execution_enabled = False
    _state.mode = TradingMode.ANALYSIS_ONLY
    return _state
