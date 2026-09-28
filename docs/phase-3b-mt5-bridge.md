# Phase 3B — MT5 Desktop Read-Only Bridge

Phone → FastAPI → MT5 Desktop/VPS → broker market data → analysis/risk engine

## Scope

This phase connects the existing analysis engine to a locally running MetaTrader 5 desktop terminal.

- Read-only candle retrieval
- MT5 terminal initialization check
- M5, M15, H1 and H4 candle mapping
- Existing technical analysis and risk logic
- Mobile-accessible API endpoints
- No order placement
- Execution remains disabled

## MT5 desktop setup

Use a Windows PC or Windows VPS with:

1. MetaTrader 5 desktop installed.
2. The Market For You account logged into the MT5 terminal.
3. Python installed.
4. The MetaTrader5 Python package installed.

Install the project dependencies, then install the optional MT5 package:

    python -m pip install -r requirements.txt
    python -m pip install MetaTrader5

Keep the MT5 terminal running and logged in.

## API checks

Check terminal connectivity:

    GET /mt5/status

Read AUDUSD M15 candles and run analysis:

    GET /mt5/live/AUDUSD?timeframe=M15&limit=200

The response contains the latest candle, deterministic analysis decision, evidence and execution_enabled: false.

## Phone access

For development, run FastAPI on the Windows/VPS host and expose it only through a private network or authenticated HTTPS reverse proxy. Do not expose an unauthenticated trading API to the public internet.

The phone does not connect to the MT5 Android application. The MT5 Python integration runs against the desktop terminal.

## Safety

This phase must not call order_send or any other trade-execution API. The kill switch and execution guard remain enabled by default.
