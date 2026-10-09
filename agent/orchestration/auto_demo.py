"""Opt-in AI-assisted automatic trading for a verified MT5 DEMO account.

AI can veto a deterministic setup, but cannot bypass risk controls or choose order size.
This worker is OFF by default and requires explicit API confirmation plus environment flags.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from api.chart_data import build_chart_payload
from market_data.models import Timeframe
from mt5.bridge.demo_execution import submit_demo_order
from mt5.bridge.market_data import MarketRequest, MetaTrader5MarketData


class AutoDemoBot:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._status: dict[str, Any] = {
            "running": False,
            "mode": "AUTO_DEMO",
            "execution_enabled": False,
            "last_check": None,
            "last_decision": "WAIT",
            "last_reason": "Bot is stopped",
            "last_order": None,
            "orders_today": 0,
            "error": None,
        }
        self._order_day = datetime.now(timezone.utc).date().isoformat()
        self._orders_today = 0
        self._day_start_balance: float | None = None
        self._last_processed_bar: dict[str, int] = {}
        self._symbol = os.getenv("AUTO_DEMO_SYMBOL", "AUDUSD").strip().upper()
        self._timeframe = Timeframe(os.getenv("AUTO_DEMO_TIMEFRAME", "M15").upper())

    def status(self) -> dict[str, Any]:
        with self._lock:
            result = dict(self._status)
            result["orders_today"] = self._orders_today
            return result

    def start(
        self, confirmation: str, symbol: str = "AUDUSD", timeframe: str = "M15"
    ) -> dict[str, Any]:
        if confirmation != "START DEMO AUTO BOT":
            raise ValueError("Exact confirmation phrase is required")
        if os.getenv("FOREX_COPILOT_ENABLE_DEMO_ORDERS", "").lower() != "true":
            raise ValueError("Set FOREX_COPILOT_ENABLE_DEMO_ORDERS=true in the local .env")
        if os.getenv("FOREX_COPILOT_ENABLE_AUTO_DEMO", "").lower() != "true":
            raise ValueError("Set FOREX_COPILOT_ENABLE_AUTO_DEMO=true to opt into auto demo")
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is required; bot will not trade without AI review")
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol.isalnum() or not 3 <= len(normalized_symbol) <= 12:
            raise ValueError("Invalid broker symbol")
        try:
            selected_timeframe = Timeframe(timeframe.upper())
        except ValueError as exc:
            raise ValueError("Supported timeframes: M5, M15, H1, H4, D1") from exc
        with self._lock:
            self._symbol = normalized_symbol
            self._timeframe = selected_timeframe
            if self._thread and self._thread.is_alive():
                return self.status()
            self._stop_event.clear()
            self._status.update(
                running=True,
                execution_enabled=True,
                last_reason="Starting; verifying MT5 demo account",
                error=None,
            )
            self._thread = threading.Thread(target=self._run, name="auto-demo-bot", daemon=True)
            self._thread.start()
        return self.status()

    def stop(self) -> dict[str, Any]:
        self._stop_event.set()
        with self._lock:
            self._status.update(
                running=False,
                execution_enabled=False,
                last_reason="Stopped by user; no new orders will be opened",
            )
        return self.status()

    def _run(self) -> None:
        try:
            while not self._stop_event.is_set():
                try:
                    self._check_once()
                except Exception as exc:  # fail closed; next interval retries safely
                    with self._lock:
                        self._status.update(
                            last_check=datetime.now(timezone.utc).isoformat(),
                            last_decision="WAIT",
                            last_reason="Safety check failed; no order placed",
                            error=f"{type(exc).__name__}: {exc}",
                        )
                self._stop_event.wait(max(15, int(os.getenv("AUTO_DEMO_POLL_SECONDS", "30"))))
        finally:
            with self._lock:
                self._status.update(running=False, execution_enabled=False)

    @staticmethod
    def _account_snapshot() -> tuple[Any, Any]:
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise RuntimeError("Install MetaTrader5 in the local Python environment") from exc
        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
        account = mt5.account_info()
        if account is None:
            mt5.shutdown()
            raise RuntimeError(f"Cannot read MT5 account: {mt5.last_error()}")
        if int(account.trade_mode) != int(mt5.ACCOUNT_TRADE_MODE_DEMO):
            mt5.shutdown()
            raise RuntimeError("AUTO BOT BLOCKED: connected MT5 account is not DEMO")
        if not bool(account.trade_allowed):
            mt5.shutdown()
            raise RuntimeError("MT5 account does not allow trading")
        positions = mt5.positions_get()
        if positions is None:
            mt5.shutdown()
            raise RuntimeError(f"Cannot read open positions: {mt5.last_error()}")
        return mt5, (account, positions)

    def _check_once(self) -> None:
        mt5, snapshot = self._account_snapshot()
        account, positions = snapshot
        try:
            today = datetime.now(timezone.utc).date().isoformat()
            if today != self._order_day:
                self._order_day = today
                self._orders_today = 0
                self._day_start_balance = float(account.balance)
            if self._day_start_balance is None:
                self._day_start_balance = float(account.balance)
            if self._orders_today >= 3:
                self._record("WAIT", "Daily order limit reached (3)", None)
                return
            if float(account.equity) <= self._day_start_balance * 0.98:
                self._record("WAIT", "Daily equity loss limit reached (2%); trading halted", None)
                self._stop_event.set()
                return
            if len(positions) >= 1:
                self._record("WAIT", "An open position already exists; one position maximum", None)
                return
            symbol = self._symbol
            timeframe = self._timeframe
            adapter = MetaTrader5MarketData()
            try:
                candles = tuple(adapter.get_candles(MarketRequest(symbol, timeframe, 300)))
            finally:
                adapter.shutdown()
            # The market-data adapter calls MT5 shutdown; reconnect before reading quotes.
            mt5, _ = self._account_snapshot()
            if len(candles) < 220:
                self._record("WAIT", "Need at least 220 candles before evaluating a setup", None)
                return
            payload = build_chart_payload(symbol, timeframe, list(candles))
            # Evaluate the last completed candle; index -1 may still be forming.
            closed = payload["candles"][-2]
            bar_time = int(closed["time"])
            if self._last_processed_bar.get(symbol) == bar_time:
                self._record("WAIT", "This completed candle was already evaluated", None)
                return
            self._last_processed_bar[symbol] = bar_time
            e20, e50 = closed["ema20"], closed["ema50"]
            close, rsi, hist, atr = (
                closed["close"], closed["rsi14"], closed["macd_histogram"], closed["atr14"]
            )
            if any(value is None for value in (e20, e50, rsi, hist, atr)) or atr <= 0:
                self._record("WAIT", "Indicators are not ready", None)
                return
            side = None
            if e20 > e50 and close > e20 and 50 <= rsi < 70 and hist > 0:
                side = "BUY"
            elif e20 < e50 and close < e20 and 30 < rsi <= 50 and hist < 0:
                side = "SELL"
            if side is None:
                self._record("WAIT", "Deterministic strategy found no complete confluence", None)
                return
            decision = self._ask_ai(symbol, timeframe.value, side, closed, payload["candles"][-12:])
            if decision.get("decision") != side or float(decision.get("confidence", 0)) < 0.75:
                self._record(
                    "WAIT", "AI did not confirm the setup with >=0.75 confidence", decision
                )
                return

            tick = mt5.symbol_info_tick(symbol)
            info = mt5.symbol_info(symbol)
            if tick is None or info is None:
                self._record("WAIT", "No current broker quote or symbol metadata", decision)
                return
            if not info.visible and not mt5.symbol_select(symbol, True):
                self._record("WAIT", "Could not select symbol in MT5", decision)
                return
            point = float(info.point)
            if point <= 0:
                self._record("WAIT", "Invalid broker point size", decision)
                return
            spread_points = (float(tick.ask) - float(tick.bid)) / point
            if spread_points > 35:
                self._record(
                    "WAIT", f"Spread {spread_points:.1f} points exceeds 35-point cap", decision
                )
                return
            entry = float(tick.ask if side == "BUY" else tick.bid)
            digits = int(info.digits)
            sl_distance = float(atr) * 1.5
            tp_distance = sl_distance * 2.0
            sl = round(entry - sl_distance if side == "BUY" else entry + sl_distance, digits)
            tp = round(entry + tp_distance if side == "BUY" else entry - tp_distance, digits)
            volume = min(0.01, float(os.getenv("AUTO_DEMO_VOLUME", "0.01")))
            if volume <= 0:
                self._record("WAIT", "Configured volume is invalid", decision)
                return
            # A stop request must be checked immediately before the side effect.
            if self._stop_event.is_set():
                self._record("WAIT", "Stop requested before order submission", decision)
                return
            # Executor independently checks demo mode, SL/TP direction, spread and <=0.5% risk.
            result = submit_demo_order(
                symbol=symbol, side=side, volume=volume, stop_loss=sl, take_profit=tp,
                orders_today=self._orders_today,
            )
            self._orders_today += 1
            self._record(
                side, "Demo order accepted; verify fill and attached SL/TP in MT5", decision
            )
            with self._lock:
                self._status["last_order"] = result
        finally:
            mt5.shutdown()

    @staticmethod
    def _ask_ai(
        symbol: str, timeframe: str, side: str, candle: dict[str, Any],
        recent: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Request a constrained JSON veto/confirm; no API response can override risk checks."""
        api_key = os.environ["OPENAI_API_KEY"]
        model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        compact = {
            "symbol": symbol, "timeframe": timeframe, "candidate": side,
            "closed_candle": {k: candle.get(k) for k in (
                "time", "open", "high", "low", "close", "ema20", "ema50",
                "ema200", "rsi14", "macd_histogram", "atr14", "volume",
            )},
            "recent_candles": [
                {
                    k: row.get(k)
                    for k in (
                        "time", "open", "high", "low", "close", "ema20", "ema50",
                        "rsi14", "macd_histogram",
                    )
                }
                for row in recent
            ],
        }
        body = {
            "model": model,
            "input": [
                {"role": "system", "content": (
                    "You are a cautious market-setup reviewer, not an order executor. "
                    "Review the supplied historical candle/indicator snapshot only. "
                    "Do not invent live news or claim certainty. Return JSON only with "
                    "decision BUY, SELL, or WAIT; confidence number 0..1; concise reason. "
                    "Confirm BUY only if the candidate BUY remains coherent; confirm SELL "
                    "only if candidate SELL remains coherent. If uncertain return WAIT."
                )},
                {"role": "user", "content": json.dumps(compact, separators=(",", ":"))},
            ],
            "text": {"format": {"type": "json_object"}},
            "max_output_tokens": 180,
        }
        request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, ValueError) as exc:
            raise RuntimeError(f"AI review failed; trade blocked: {exc}") from exc
        text_parts = [
            part.get("text", "")
            for item in raw.get("output", [])
            for part in item.get("content", [])
            if part.get("type") == "output_text"
        ]
        if not text_parts:
            raise RuntimeError("AI returned no structured review; trade blocked")
        result = json.loads(text_parts[0])
        decision = str(result.get("decision", "WAIT")).upper()
        if decision not in {"BUY", "SELL", "WAIT"}:
            decision = "WAIT"
        try:
            confidence = max(0.0, min(1.0, float(result.get("confidence", 0))))
        except (TypeError, ValueError):
            confidence = 0.0
        return {
            "decision": decision,
            "confidence": confidence,
            "reason": str(result.get("reason", ""))[:400],
        }

    def _record(self, decision: str, reason: str, ai: Any) -> None:
        with self._lock:
            self._status.update(
                last_check=datetime.now(timezone.utc).isoformat(),
                last_decision=decision,
                last_reason=reason,
                ai_review=ai,
                error=None,
                orders_today=self._orders_today,
            )


auto_demo_bot = AutoDemoBot()
