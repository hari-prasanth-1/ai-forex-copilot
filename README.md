# AI Forex Copilot

AI-assisted Forex market analysis and demo-trading platform.

## Branch Strategy

- `main` — protected production/release branch. Do not develop directly on `main`.
- `develop` — integration branch for tested development work.
- `feature/*` — short-lived branches for individual features or fixes.

### Development Flow

```text
feature/*
    ↓ Pull Request
develop
    ↓ Tests + Backtest + Review
main
    ↓
Demo / Production deployment
```

## Initial Scope

Phase 1 will focus on analysis and risk controls with automated order execution disabled by default.

Planned capabilities include:

- MT5 market-data integration
- Multi-timeframe technical analysis
- EMA 20/50/200, RSI, MACD, ATR and volume
- Support/resistance and market-structure analysis
- Breakout/pullback and price-action analysis
- AI-assisted trade reasoning
- Risk/reward and position-sizing checks
- BUY / SELL / NO TRADE signals
- Backtesting foundation
- Automated tests and CI
- Demo-only execution before any live-trading consideration

## Safety

This project is intended to be developed and tested against a demo account first. Live trading must remain explicitly disabled until the system has been independently validated through backtesting and extended forward testing.
