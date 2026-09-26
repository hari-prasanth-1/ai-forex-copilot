"""Minimal API boundary for the mobile/PWA client."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AI Forex Copilot API", version="0.1.0")


class HealthResponse(BaseModel):
    status: str
    execution_enabled: bool
    timestamp: datetime


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        execution_enabled=False,
        timestamp=datetime.now(UTC),
    )
