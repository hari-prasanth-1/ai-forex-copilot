# AI-assisted MT5 Auto Demo Bot

## Important
This is an experimental **demo-account-only** bot, not a profit guarantee. Keep it stopped until you have reviewed the risk controls and observed paper/backtest results. Do not use a live account. The worker refuses to trade unless MT5 explicitly reports DEMO mode.

## Architecture
1. The local Windows machine runs MT5 Desktop and the FastAPI app.
2. The read-only bridge loads MT5 candles.
3. A deterministic EMA20/EMA50 + price/EMA20 + RSI + MACD confluence strategy identifies a candidate.
4. OpenAI Responses API reviews only candidate setups. An API failure, malformed response, WAIT, wrong side, or confidence below 0.75 blocks the trade.
5. A separate executor checks demo mode, quote/spread, SL/TP direction, broker stop distance and estimated SL risk before sending the order.

The model cannot set volume, bypass risk checks, or send orders itself.

## Safety caps
- OFF by default. Requires both environment flags and exact dashboard confirmation.
- AUDUSD and M15 are defaults; the dashboard lets you choose symbol/timeframe.
- Maximum 0.01 lots; each order's estimated stop-loss risk <=0.5% of account balance.
- Mandatory SL/TP, ATR-derived 1.5x stop and 2R target.
- Spread <=35 points, at most one open account position, max three orders per UTC day.
- Stop the worker at 2% equity decline from its recorded day-start balance.
- AI error means no trade; stop button prevents new orders.

## Setup (Windows / MT5 desktop)
1. Ensure MT5 is logged in to the broker's DEMO account, Algo Trading is allowed if required, and the symbol is visible in Market Watch.
2. Activate the project's virtual environment and install dependencies: `python -m pip install -r requirements.txt`
3. Install the optional MT5 package on the same Windows Python environment: `python -m pip install MetaTrader5`
4. Copy `.env.example` to `.env`; put your API key in `OPENAI_API_KEY`. Configure model/cost controls in the OpenAI API project. Do not paste keys into chat or commit them.
5. First leave both flags false and run tests/backtests. For a deliberate demo forward-test only, set `FOREX_COPILOT_ENABLE_DEMO_ORDERS=true` and `FOREX_COPILOT_ENABLE_AUTO_DEMO=true` in `.env`.
6. Start API from the repository root: `uvicorn api.app:app --env-file .env --host 127.0.0.1 --port 8000`
7. Open `http://127.0.0.1:8000`, review bot status and click Start demo bot. Confirm the exact phrase shown by the UI. Use Stop bot to stop new orders.
8. Verify each actual fill, attached SL/TP, account history and P&L inside MT5. API status is not a substitute for broker confirmation.

## Known limitations before any extended unattended demo
- Order/day and day-start balance tracking are in process memory; restarting the API resets them. Do not use unattended until a persistent, broker-reconciled ledger is implemented.
- The bot evaluates one symbol at a time, permits only one open position across the account, and evaluates the last completed candle for the selected timeframe.
- Broker-specific filling modes and symbol suffixes may require adaptation.
- No performance or profitability claim is made. Backtest with spread/commission/slippage and run forward tests before considering any further automation.
- Do not expose this API to the public internet; it has no user authentication.
