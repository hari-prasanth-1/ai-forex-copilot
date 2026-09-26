# AI Forex Copilot

AI-assisted Forex market-analysis and demo-trading platform designed to combine deterministic market-data/technical analysis, an AI reasoning layer, strict risk controls, backtesting, and a controlled MT5 execution path.

> **Important:** This project is a software-engineering and research system, not a promise of profitable trading. Development starts with demo trading and automated order execution disabled. Live trading is a separate future stage that requires extensive validation.

## 1. Project Vision

Build a modular AI Forex co-pilot that can:

- collect and normalize market data;
- analyze multiple timeframes and market structure;
- calculate technical indicators and price-action signals;
- identify setups such as trend continuation, breakout, pullback and reversal candidates;
- use an AI model to explain and synthesize the evidence rather than blindly generate orders;
- apply deterministic risk and trade-validation rules before any order can be considered;
- backtest strategies and maintain a trade journal;
- integrate with MT5 for demo-market data and, later, controlled demo execution;
- expose analysis and controls through an API/mobile-friendly interface;
- support TradingView/webhook inputs where useful;
- provide observability, audit logs, tests and CI/CD from the beginning.

## 2. Target Initial Environment

The first implementation is intentionally narrow so that the system can be tested properly.

- Broker: Markets4you demo environment
- Platform: MetaTrader 5 (MT5)
- Initial instrument: AUDUSD
- Initial timeframes: M15 and H1
- Future scanner instruments: EURUSD, GBPUSD, USDJPY, XAUUSD and other supported symbols
- Initial execution mode: analysis only / demo-only
- Automated order execution: **OFF by default**

The architecture should remain broker-agnostic where practical so that the market-analysis engine is not tightly coupled to one broker.

## 3. High-Level Architecture

```text
                    ┌──────────────────────────────┐
                    │        MT5 / Market Data     │
                    │   candles • ticks • volume   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │       Market Data Layer      │
                    │ normalize • validate • cache │
                    └──────────────┬───────────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │ Indicators     │ │ Market         │ │ Price Action   │
        │ EMA RSI MACD   │ │ Structure      │ │ S/R Breakout   │
        │ ATR Volume     │ │ Trend/Regime   │ │ Pullback       │
        └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
                └──────────────────┼──────────────────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │      Signal / Setup Engine   │
                    │ BUY • SELL • NO TRADE       │
                    └──────────────┬───────────────┘
                                   │
                      ┌────────────┴────────────┐
                      ▼                         ▼
             ┌────────────────┐        ┌──────────────────┐
             │ Risk Engine    │        │ News / Volatility│
             │ SL TP R:R size │        │ filter           │
             └───────┬────────┘        └────────┬─────────┘
                     └──────────────┬────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ AI Reasoning Layer  │
                         │ explain / synthesize│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Decision Gateway    │
                         │ policy + safeguards │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    ▼               ▼                ▼
               Analysis        User Confirm      Demo EA
                 only              mode          / Bridge
                                    │                │
                                    └───────┬────────┘
                                            ▼
                                      MT5 Demo Order
```

The AI layer is not the only source of truth for risk. Deterministic safeguards remain outside the model so that model output cannot bypass hard trading limits.

## 4. Core Modules

### 4.1 Market Data

Responsibilities:

- MT5 candle/tick retrieval;
- OHLCV normalization;
- timeframe handling;
- symbol metadata and trading-session awareness;
- stale/missing-data detection;
- caching and data validation;
- future adapters for other providers.

### 4.2 Technical Analysis

Initial indicators:

- EMA 20 / 50 / 200
- RSI
- MACD
- ATR
- volume / tick-volume analysis

The engine should return structured values and signals rather than unstructured text so that they can be tested independently.

### 4.3 Market Structure & Price Action

Planned analysis includes:

- higher-high / higher-low and lower-high / lower-low structure;
- trend and range detection;
- support/resistance zones;
- swing highs/lows;
- breakout and false-breakout context;
- pullback/retest setups;
- candlestick/price-action context;
- multi-timeframe alignment.

### 4.4 Signal Engine

The signal engine combines deterministic evidence into a structured setup:

- `BUY`
- `SELL`
- `NO_TRADE`

Each setup should contain evidence, timeframe context, invalidation level, proposed stop-loss/take-profit levels, risk/reward information and a confidence/evidence summary. Confidence must not be treated as a guarantee of outcome.

### 4.5 AI Reasoning Layer

The AI model is used to synthesize structured market evidence, explain conflicting signals, identify missing context and produce a human-readable analysis.

The model should receive structured inputs rather than raw unrestricted market state whenever possible. AI calls should be event-driven/filtered instead of being made on every market tick to control cost and latency.

The model must not be allowed to bypass deterministic risk limits or directly override execution safeguards.

### 4.6 Risk Engine

The risk engine is a hard safety boundary.

Planned checks:

- account balance/equity;
- maximum risk per trade;
- stop-loss distance;
- take-profit distance;
- risk/reward ratio;
- position sizing;
- maximum open positions;
- duplicate-position protection;
- daily loss / drawdown limits;
- spread/slippage checks;
- trading-session restrictions;
- news/volatility restrictions;
- emergency kill switch.

The engine should return an explicit allow/reject decision with machine-readable reasons.

### 4.7 News & Volatility Filter

Future integration can use economic-calendar/news sources to detect periods where volatility or event risk makes a setup unsuitable. The system should record the source timestamp and avoid pretending that news data is real-time when it is not.

### 4.8 Backtesting

The backtesting layer will support:

- historical candle replay;
- strategy configuration;
- spread/fee assumptions;
- stop-loss/take-profit simulation;
- position sizing;
- performance metrics;
- trade-by-trade logs;
- parameter experiments;
- walk-forward/forward-testing foundations.

Backtests must avoid look-ahead bias and clearly separate in-sample and out-of-sample results.

### 4.9 MT5 Integration

The execution architecture will be designed around an MT5 bridge/EA rather than fragile screen-click automation.

Planned modes:

1. **Analysis Only** — market analysis and signals; no order submission.
2. **Assisted Demo** — signal is produced, user confirms, then the demo execution path can submit the order.
3. **Auto Demo** — risk engine and policy gateway approve the setup before a demo order is submitted.

Live trading is not part of the initial implementation.

### 4.10 API / Mobile Control Layer

A mobile-friendly control surface is planned for:

- current market state;
- active setups;
- analysis history;
- risk status;
- demo positions;
- trade journal;
- system health;
- mode selection;
- emergency stop.

The control layer should communicate with the backend/bridge rather than depending on direct automation of the MT5 mobile application's UI.

### 4.11 TradingView / Webhooks

Where useful and supported, TradingView alerts can act as an additional signal/input source through a webhook endpoint. Webhook payloads should be validated, authenticated and logged before entering the signal pipeline.

## 5. Trading Modes & Safety Model

```text
Analysis Only
    ↓
Signal + Evidence
    ↓
Risk Validation
    ↓
Human Review

Assisted Demo
    ↓
Signal + Evidence
    ↓
Risk Validation
    ↓
User Confirmation
    ↓
MT5 Demo

Auto Demo
    ↓
Signal + Evidence
    ↓
Risk Validation
    ↓
Policy Gateway
    ↓
MT5 Demo
```

Auto-execution must have independent enable/disable controls and a kill switch. Secrets, broker credentials and API keys must never be committed to Git.

## 6. Development Phases

### Phase 0 — Repository & Engineering Foundation

- branch strategy;
- project documentation;
- Python project structure;
- configuration management;
- `.env.example` and secret handling;
- logging and error handling;
- unit-test framework;
- lint/type-check setup;
- GitHub Actions CI.

### Phase 1 — Market Analysis Foundation

- MT5 data adapter;
- AUDUSD M15/H1;
- EMA, RSI, MACD, ATR and volume;
- support/resistance;
- market structure;
- breakout/pullback detection;
- structured BUY/SELL/NO_TRADE output;
- initial risk engine;
- AI analysis interface;
- backtesting foundation;
- execution remains OFF.

### Phase 2 — Demo Integration

- MT5 EA/bridge;
- demo account connectivity;
- assisted demo mode;
- order validation;
- position and order state synchronization;
- trade journal;
- monitoring and alerts.

### Phase 3 — Multi-Pair Scanner

- EURUSD;
- GBPUSD;
- USDJPY;
- XAUUSD;
- configurable symbol list;
- setup ranking by evidence without presenting the ranking as a guarantee of profitability;
- session and volatility filters.

### Phase 4 — Advanced AI & Research

- richer market-regime detection;
- structured AI explanations;
- setup clustering;
- news/context integration;
- experiment tracking;
- improved backtesting and walk-forward evaluation.

### Phase 5 — Long Forward Testing

- extended demo operation;
- reliability monitoring;
- slippage/spread analysis;
- drawdown analysis;
- failure-mode testing;
- review of model and strategy changes.

Any future live-trading consideration is gated on documented validation and remains a separate deployment decision.

## 7. Repository Structure

```text
ai-forex-copilot/
├── agent/
│   ├── analysis/
│   ├── strategies/
│   ├── risk/
│   └── prompts/
├── market_data/
├── mt5/
│   ├── ea/
│   └── bridge/
├── backtesting/
├── api/
├── mobile/
├── tests/
├── config/
├── docs/
├── .github/
│   └── workflows/
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

The exact structure can evolve as implementation details become clearer; module boundaries should remain testable and loosely coupled.

## 8. CI/CD & Git Workflow

```text
feature/*
    ↓ PR
   develop
    ↓
Automated Tests
    ↓
Backtest / Validation
    ↓
Demo
    ↓ PR
   main
    ↓
Release / Deployment
```

Rules:

- no direct feature development on `main`;
- feature work uses `feature/*` branches;
- PRs target `develop` first;
- CI must run before merge;
- strategy/backtest changes require validation evidence;
- `main` represents releasable code;
- deployment credentials stay outside source control.

## 9. Testing Strategy

Testing will include:

- unit tests for indicators and calculations;
- market-structure tests;
- strategy/setup tests;
- risk-engine tests;
- data-validation tests;
- backtest regression tests;
- API tests;
- MT5 bridge integration tests where practical;
- failure and kill-switch tests;
- security/static-analysis checks in CI.

Important financial calculations should be deterministic and independently testable without requiring an AI model.

## 10. Observability & Auditability

The system should record:

- market-data timestamps;
- indicator inputs/outputs;
- setup evidence;
- AI request/response metadata where safe;
- risk-engine decisions and rejection reasons;
- order requests/results;
- position state changes;
- errors and system health;
- strategy/configuration version.

Sensitive credentials and unnecessary personal data must not be logged.

## 11. Security

Security requirements include:

- secrets only through environment/secret-management mechanisms;
- no broker/API credentials in Git;
- webhook authentication and validation;
- least-privilege service accounts;
- protected production branch;
- dependency and code scanning;
- secure API authentication;
- audit logging;
- emergency execution disablement.

## 12. Configuration

Configuration should control, at minimum:

- broker/environment;
- symbols;
- timeframes;
- indicator parameters;
- risk limits;
- execution mode;
- AI provider/model;
- news provider;
- logging level;
- feature flags.

Safe defaults must keep automated order execution disabled.

## 13. Success Criteria

The project should not be judged only by whether it produces BUY/SELL signals. Key engineering criteria are:

- reproducible calculations;
- reliable market-data handling;
- correct risk enforcement;
- backtest integrity;
- stable MT5 synchronization;
- transparent reasoning/evidence;
- strong test coverage for critical paths;
- secure secret handling;
- observable and auditable operation;
- safe failure behaviour.

Trading performance should be evaluated separately using appropriate historical and forward-testing methodology.

## 14. Current Status

- [x] GitHub repository created
- [x] `main` initialized with README
- [x] `develop` branch created from `main`
- [ ] `feature/phase-1-foundation`
- [ ] Phase 1 implementation
- [ ] CI pipeline
- [ ] MT5 data integration
- [ ] Backtesting foundation
- [ ] Demo execution integration

## 15. Guiding Principles

1. **Safety before automation.**
2. **Deterministic risk controls outside the AI model.**
3. **Demo first, live later if separately validated.**
4. **Backtest and forward-test before changing execution mode.**
5. **Never commit secrets.**
6. **Keep the system modular and broker-agnostic where practical.**
7. **Every automated action must be observable and auditable.**
8. **AI assists analysis; it does not bypass hard safety rules.**
