"""Mobile-ready API boundary for the Forex Copilot."""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import FastAPI, HTTPException, Query\nfrom fastapi.responses import FileResponse\nfrom fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from market_data.models import Timeframe


class TradingMode(StrEnum):
    ANALYSIS_ONLY = "analysis_only"
    ASSISTED_DEMO = "assisted_demo"
    AUTO_DEMO = "auto_demo"


class ModeRequest(BaseModel):
    mode: TradingMode


class AnalysisResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    decision: str = "NO_TRADE"
    execution_enabled: bool = False
    message: str


class RiskResponse(BaseModel):
    allowed: bool = False
    reason: str
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


@app.get("/risk", response_model=RiskResponse)
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
