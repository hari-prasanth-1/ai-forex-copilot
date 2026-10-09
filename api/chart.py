"""Read-only chart endpoint for the phone-first dashboard."""
from fastapi import APIRouter, HTTPException, Query

from api.chart_data import load_mt5_chart
from market_data.models import Timeframe

router = APIRouter()


@router.get("/mt5/chart/{symbol}")
def mt5_chart(
    symbol: str,
    timeframe: Timeframe = Query(default=Timeframe.M15),
    limit: int = Query(default=200, ge=50, le=5000),
):
    try:
        return load_mt5_chart(symbol.upper(), timeframe, limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MT5 chart data error: {exc}") from exc
