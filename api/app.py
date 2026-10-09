"""Mobile-ready API boundary for the Forex Copilot."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent.orchestration.auto_demo import auto_demo_bot
from api.chart import router as chart_router
from api.services import build_analysis
from market_data.models import Candle, Timeframe
from mt5.bridge.demo_execution import ExecutionRejected, submit_demo_order
from mt5.bridge.market_data import MarketRequest, MetaTrader5MarketData


class TradingMode(StrEnum):
    ANALYSIS_ONLY = "analysis_only"
    ASSISTED_DEMO = "assisted_demo"
    AUTO_DEMO = "auto_demo"


class ModeRequest(BaseModel):
    mode: TradingMode


class CandleRequest(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = Field(ge=0)


class CandleAnalysisRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    timeframe: Timeframe = Timeframe.M15
    candles: list[CandleRequest] = Field(min_length=1, max_length=5000)


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


class MT5LiveResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    candles: int
    decision: str
    latest_close: float | None = None
    evidence: list[str] = Field(default_factory=list)
    source: str = "mt5_terminal"
    execution_enabled: bool = False


class LivePaperResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    candles: int
    decision: str
    latest_close: float | None = None
    evidence: list[str] = Field(default_factory=list)
    execution_enabled: bool = False


class DemoArmRequest(BaseModel):
    confirmation: str


class DemoOrderRequest(BaseModel):
    symbol: str = Field(min_length=3, max_length=12)
    side: str
    volume: float = Field(gt=0, le=0.01)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    confirmation: str


class SafetyState(BaseModel):
    mode: TradingMode = TradingMode.ANALYSIS_ONLY
    kill_switch: bool = True
    execution_enabled: bool = False


app = FastAPI(title="AI Forex Copilot API", version="0.3.0")
app.include_router(chart_router)
app.mount("/static", StaticFiles(directory="api/static"), name="static")
_state = SafetyState()
_demo_order_count = 0
_demo_order_date = datetime.now(timezone.utc).date()


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse("api/static/index.html")


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


@app.post("/analysis", response_model=AnalysisResponse)
def analysis_from_candles(request: CandleAnalysisRequest) -> AnalysisResponse:
    candles = [
        Candle(c.timestamp, c.open, c.high, c.low, c.close, c.volume)
        for c in request.candles
    ]
    setup = build_analysis(request.symbol.upper(), request.timeframe.value, candles)
    return AnalysisResponse(
        symbol=setup.symbol,
        timeframe=request.timeframe,
        decision=setup.signal.value,
        message="; ".join(setup.evidence),
    )


@app.get("/mt5/status")
def mt5_status() -> dict[str, Any]:
    """Check whether the local MT5 terminal can be initialized."""
    try:
        market_data = MetaTrader5MarketData()
        connected = market_data.connected
        market_data.shutdown()
        return {
            "connected": connected,
            "data_source": "mt5_terminal",
            "execution_enabled": False,
        }
    except Exception as exc:
        return {
            "connected": False,
            "data_source": "mt5_terminal",
            "execution_enabled": False,
            "error": str(exc),
        }


@app.get("/mt5/live/{symbol}", response_model=MT5LiveResponse)
def mt5_live(
    symbol: str,
    timeframe: Timeframe = Query(default=Timeframe.M15),
    limit: int = Query(default=200, ge=50, le=5000),
) -> MT5LiveResponse:
    """Read actual MT5 terminal candles and run analysis without order placement."""
    market_data = MetaTrader5MarketData()
    try:
        candles = tuple(
            market_data.get_candles(
                MarketRequest(symbol=symbol.upper(), timeframe=timeframe, limit=limit)
            )
        )
        setup = build_analysis(symbol.upper(), timeframe.value, candles)
        return MT5LiveResponse(
            symbol=setup.symbol,
            timeframe=timeframe,
            candles=len(candles),
            decision=setup.signal.value,
            latest_close=candles[-1].close if candles else None,
            evidence=list(setup.evidence),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MT5 market-data error: {exc}") from exc
    finally:
        market_data.shutdown()


@app.get("/paper/live/{symbol}", response_model=LivePaperResponse)
def paper_live(
    symbol: str,
    timeframe: Timeframe = Query(default=Timeframe.M15),
    limit: int = Query(default=200, ge=50, le=5000),
) -> LivePaperResponse:
    market_data = MetaTrader5MarketData()
    candles = tuple(
        market_data.get_candles(
            MarketRequest(symbol=symbol.upper(), timeframe=timeframe, limit=limit)
        )
    )
    setup = build_analysis(symbol.upper(), timeframe.value, candles)
    return LivePaperResponse(
        symbol=setup.symbol,
        timeframe=timeframe,
        candles=len(candles),
        decision=setup.signal.value,
        latest_close=candles[-1].close if candles else None,
        evidence=list(setup.evidence),
    )



@app.post("/demo/arm", response_model=SafetyState)
def arm_demo(request: DemoArmRequest) -> SafetyState:
    """Explicitly arm assisted demo mode; the executor independently verifies demo account."""
    if request.confirmation != "I CONFIRM DEMO ONLY":
        raise HTTPException(status_code=400, detail="Exact confirmation phrase is required")
    if os.getenv("FOREX_COPILOT_ENABLE_DEMO_ORDERS", "").lower() != "true":
        raise HTTPException(
            status_code=403,
            detail="Set FOREX_COPILOT_ENABLE_DEMO_ORDERS=true locally to opt into demo execution",
        )
    _state.mode = TradingMode.ASSISTED_DEMO
    _state.kill_switch = False
    _state.execution_enabled = True
    return _state


@app.post("/demo/order")
def demo_order(request: DemoOrderRequest) -> dict[str, Any]:
    """Place only an explicitly confirmed, risk-capped order on a verified MT5 DEMO account."""
    global _demo_order_count, _demo_order_date
    demo_not_armed = (
        _state.kill_switch
        or not _state.execution_enabled
        or _state.mode != TradingMode.ASSISTED_DEMO
    )
    if demo_not_armed:
        raise HTTPException(
            status_code=423,
            detail="Demo execution is not armed; kill switch is active",
        )
    if request.confirmation != "PLACE DEMO ORDER":
        raise HTTPException(status_code=400, detail="Exact order confirmation phrase is required")
    today = datetime.now(timezone.utc).date()
    if today != _demo_order_date:
        _demo_order_date = today
        _demo_order_count = 0
    try:
        result = submit_demo_order(
            symbol=request.symbol,
            side=request.side,
            volume=request.volume,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            orders_today=_demo_order_count,
        )
        _demo_order_count += 1
        return result
    except ExecutionRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MT5 demo execution error: {exc}") from exc


@app.get("/risk", response_model=RiskResponse)
def risk() -> RiskResponse:
    return RiskResponse(reason="No trade approved; execution is disabled")


@app.get("/mode", response_model=SafetyState)
def mode() -> SafetyState:
    return _state


@app.post("/mode", response_model=SafetyState)
def set_mode(request: ModeRequest) -> SafetyState:
    _state.mode = request.mode
    _state.execution_enabled = False
    return _state


@app.post("/kill-switch", response_model=SafetyState)
def kill_switch() -> SafetyState:
    _state.kill_switch = True
    _state.execution_enabled = False
    _state.mode = TradingMode.ANALYSIS_ONLY
    return _state


@app.get("/mobile/live/{symbol}")
def mobile_live(
    symbol: str,
    timeframe: Timeframe = Query(default=Timeframe.M15),
    limit: int = Query(default=200, ge=50, le=5000),
) -> dict[str, Any]:
    """Run read-only analysis using the phone-friendly market-data adapter."""
    from api.mobile_market import build_mobile_analysis

    try:
        return build_mobile_analysis(symbol.upper(), timeframe, limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"mobile market-data error: {exc}") from exc



class AutoDemoStartRequest(BaseModel):
    confirmation: str
    symbol: str = Field(default="AUDUSD", min_length=3, max_length=12)
    timeframe: Timeframe = Timeframe.M15


@app.get("/auto-demo/status")
def auto_demo_status() -> dict[str, Any]:
    """Read automatic demo-bot status; never starts execution."""
    return auto_demo_bot.status()


@app.post("/auto-demo/start")
def auto_demo_start(request: AutoDemoStartRequest) -> dict[str, Any]:
    """Start the opt-in AI-reviewed demo-only worker."""
    try:
        return auto_demo_bot.start(request.confirmation, request.symbol, request.timeframe.value)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/auto-demo/stop")
def auto_demo_stop() -> dict[str, Any]:
    """Stop new automatic demo orders immediately."""
    return auto_demo_bot.stop()
