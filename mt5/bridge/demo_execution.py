"""Explicitly gated MT5 demo-order execution with conservative guardrails.

This module never runs automatically. The caller must pass the API safety gates,
the environment opt-in must be enabled, and the connected account must be DEMO.
"""
from datetime import datetime, timezone
from typing import Any

import os
import re


MAX_VOLUME = 0.01
MAX_RISK_FRACTION = 0.005
MAX_ORDERS_PER_DAY = 3
MAX_SPREAD_POINTS = 35
_ALLOWED_SYMBOL = re.compile(r"^[A-Z0-9.]{3,12}$")


class ExecutionRejected(RuntimeError):
    """A safety check prevented an order from being sent."""


def _mt5_module() -> Any:
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise ExecutionRejected("Install MetaTrader5 in the local Python environment") from exc
    return mt5


def _ensure_demo_account(mt5: Any) -> Any:
    if os.getenv("FOREX_COPILOT_ENABLE_DEMO_ORDERS", "").lower() != "true":
        raise ExecutionRejected(
            "Demo order execution is disabled. Set FOREX_COPILOT_ENABLE_DEMO_ORDERS=true "
            "only for a dedicated demo terminal."
        )
    if not mt5.initialize():
        raise ExecutionRejected(f"MT5 initialize failed: {mt5.last_error()}")
    account = mt5.account_info()
    if account is None:
        mt5.shutdown()
        raise ExecutionRejected(f"Cannot read MT5 account: {mt5.last_error()}")
    demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0)
    if int(getattr(account, "trade_mode", -1)) != int(demo_mode):
        mt5.shutdown()
        raise ExecutionRejected("Refusing order: connected MT5 account is not DEMO mode")
    if not bool(getattr(account, "trade_allowed", False)):
        mt5.shutdown()
        raise ExecutionRejected("Trading is not allowed for this MT5 account")
    return account


def submit_demo_order(
    *,
    symbol: str,
    side: str,
    volume: float,
    stop_loss: float,
    take_profit: float,
    orders_today: int,
) -> dict[str, Any]:
    """Submit one explicitly requested demo market order after strict validation."""
    normalized = symbol.strip().upper()
    direction = side.strip().upper()
    if not _ALLOWED_SYMBOL.fullmatch(normalized):
        raise ExecutionRejected("Invalid symbol")
    if direction not in {"BUY", "SELL"}:
        raise ExecutionRejected("side must be BUY or SELL")
    if not 0 < volume <= MAX_VOLUME:
        raise ExecutionRejected(f"volume must be greater than 0 and at most {MAX_VOLUME}")
    if orders_today >= MAX_ORDERS_PER_DAY:
        raise ExecutionRejected(f"Daily order limit reached ({MAX_ORDERS_PER_DAY})")
    if stop_loss <= 0 or take_profit <= 0:
        raise ExecutionRejected("Stop-loss and take-profit are required and must be positive")

    mt5 = _mt5_module()
    account = _ensure_demo_account(mt5)
    try:
        info = mt5.symbol_info(normalized)
        tick = mt5.symbol_info_tick(normalized)
        if info is None or tick is None:
            raise ExecutionRejected(f"Symbol {normalized} is not available in this broker terminal")
        if not info.visible and not mt5.symbol_select(normalized, True):
            raise ExecutionRejected(f"Could not select symbol {normalized}")
        point = float(info.point)
        digits = int(info.digits)
        if point <= 0:
            raise ExecutionRejected("Broker returned an invalid point size")
        spread_points = (float(tick.ask) - float(tick.bid)) / point
        if spread_points > MAX_SPREAD_POINTS:
            raise ExecutionRejected(
                f"Spread too high ({spread_points:.1f} points; limit {MAX_SPREAD_POINTS})"
            )

        is_buy = direction == "BUY"
        entry = float(tick.ask if is_buy else tick.bid)
        sl, tp = round(float(stop_loss), digits), round(float(take_profit), digits)
        stop_level = int(getattr(info, "trade_stops_level", 0) or 0) * point
        if is_buy and not (sl < entry - stop_level and tp > entry + stop_level):
            raise ExecutionRejected(
                "BUY requires stop-loss below entry and take-profit above entry"
            )
        if not is_buy and not (sl > entry + stop_level and tp < entry - stop_level):
            raise ExecutionRejected(
                "SELL requires stop-loss above entry and take-profit below entry"
            )

        order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL
        estimated_loss = mt5.order_calc_profit(order_type, normalized, volume, entry, sl)
        if estimated_loss is None or float(estimated_loss) >= 0:
            raise ExecutionRejected("Could not calculate a valid stop-loss risk; order blocked")
        risk_cash = abs(float(estimated_loss))
        balance = float(account.balance)
        if balance <= 0 or risk_cash > balance * MAX_RISK_FRACTION:
            raise ExecutionRejected(
                f"Stop-loss risk {risk_cash:.2f} exceeds the {MAX_RISK_FRACTION:.1%} balance limit"
            )

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": normalized,
            "volume": float(volume),
            "type": order_type,
            "price": entry,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 610091,
            "comment": "ForexCopilot demo-only",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": getattr(info, "filling_mode", mt5.ORDER_FILLING_RETURN),
        }
        check = mt5.order_check(request)
        if check is None or int(getattr(check, "retcode", -1)) != 0:
            raise ExecutionRejected(
                "Broker order_check rejected the order: "
                f"{getattr(check, 'comment', mt5.last_error())}"
            )
        result = mt5.order_send(request)
        if result is None:
            raise ExecutionRejected(f"Broker did not return an order result: {mt5.last_error()}")
        success_codes = {
            getattr(mt5, "TRADE_RETCODE_DONE", 10009),
            getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", 10010),
            getattr(mt5, "TRADE_RETCODE_PLACED", 10008),
        }
        if int(result.retcode) not in success_codes:
            raise ExecutionRejected(
                f"Broker rejected the order ({result.retcode}): {getattr(result, 'comment', '')}"
            )
        return {
            "status": "submitted",
            "account_mode": "DEMO",
            "symbol": normalized,
            "side": direction,
            "volume": float(volume),
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "estimated_risk": risk_cash,
            "order": int(getattr(result, "order", 0)),
            "deal": int(getattr(result, "deal", 0)),
            "execution_enabled": True,
            "message": "Demo order submitted; verify fill and attached SL/TP in MT5.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        mt5.shutdown()
