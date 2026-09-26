# Mobile Client

The primary user interface is designed for phone-first usage.

## Target platforms

- Android and iOS through a responsive PWA/web app
- Desktop browsers as an optional experience
- Future native packaging can reuse the same API contracts

## Initial screens

1. Dashboard — market/session status and system health
2. Signal — BUY / SELL / NO TRADE with evidence and invalidation
3. Risk — risk-per-trade, daily loss limit, exposure and kill switch
4. Positions — demo positions and P&L
5. Journal — trade decisions and reasoning history
6. Settings — symbols, timeframes, mode and safe feature flags

The mobile client never stores broker passwords or makes direct MT5 order calls. All trading actions must pass through the authenticated backend and deterministic risk boundary.
