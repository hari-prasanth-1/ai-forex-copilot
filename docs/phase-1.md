# Phase 1 — Foundation

Phase 1 builds the deterministic analysis and risk foundation for the AI Forex Copilot.

## Included

- Python project/tooling setup
- Technical indicators: EMA, RSI, MACD, ATR
- Structured trade setup model
- Deterministic analysis engine
- Deterministic risk engine
- Backtesting contract with sequential candle access
- AI reasoning interface
- MT5 execution boundary
- Unit tests
- GitHub Actions CI

## Explicitly excluded

- Live trading
- Automatic demo order submission
- Broker credential storage in Git
- Direct MT5 mobile UI automation
- Unvalidated AI-driven execution

## Safety invariant

`AUTO_EXECUTION_ENABLED=false` is the default configuration. The Phase 1 MT5 adapter raises an explicit execution-disabled error instead of submitting an order.

## Next implementation work

1. Add typed OHLCV market-data models.
2. Add MT5 read-only data adapter.
3. Add support/resistance and market-structure detectors.
4. Add ATR-based stop and position-sizing integration.
5. Add a real backtest runner and performance metrics.
6. Add AI provider implementation behind the existing interface.
7. Add integration tests around the read-only MT5 boundary.
