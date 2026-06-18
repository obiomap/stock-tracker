"""
Alpaca brokerage integration — paper & live trading.

Configure via environment variables (set in Railway or .env):
  ALPACA_API_KEY    — Alpaca API key ID
  ALPACA_API_SECRET — Alpaca API secret
  ALPACA_PAPER      — "true" (default) for paper trading, "false" for live

WARNING: setting ALPACA_PAPER=false submits real orders with real money.
"""

import os
from typing import Optional


def is_configured() -> bool:
    return bool(os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_API_SECRET"))


def is_paper() -> bool:
    return os.environ.get("ALPACA_PAPER", "true").lower() != "false"


def _client():
    from alpaca.trading.client import TradingClient
    return TradingClient(
        os.environ["ALPACA_API_KEY"],
        os.environ["ALPACA_API_SECRET"],
        paper=is_paper(),
    )


def place_order(symbol: str, qty: float, side: str) -> dict:
    """
    Submit a day market order.
    side = 'BUY' or 'SELL'. Returns {ok, id, status, symbol, qty, side, paper}.
    """
    if not is_configured():
        return {"ok": False, "error": "Alpaca API credentials not configured — set ALPACA_API_KEY and ALPACA_API_SECRET"}
    if qty <= 0:
        return {"ok": False, "error": "Quantity must be greater than 0"}
    try:
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        order = _client().submit_order(req)
        return {
            "ok":     True,
            "id":     str(order.id),
            "status": str(order.status),
            "symbol": order.symbol,
            "qty":    float(order.qty or qty),
            "side":   side.upper(),
            "paper":  is_paper(),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_positions() -> list[dict]:
    """Return all open positions or [] on error / not configured."""
    if not is_configured():
        return []
    try:
        return [
            {
                "symbol":          p.symbol,
                "qty":             float(p.qty),
                "avg_entry":       float(p.avg_entry_price),
                "current_price":   float(p.current_price or 0),
                "unrealized_pl":   float(p.unrealized_pl or 0),
                "unrealized_plpc": float(p.unrealized_plpc or 0) * 100,
                "market_value":    float(p.market_value or 0),
            }
            for p in _client().get_all_positions()
        ]
    except Exception:
        return []


def get_account() -> Optional[dict]:
    """Return account summary or None on error / not configured."""
    if not is_configured():
        return None
    try:
        a = _client().get_account()
        return {
            "cash":            float(a.cash),
            "portfolio_value": float(a.portfolio_value),
            "buying_power":    float(a.buying_power),
            "paper":           is_paper(),
        }
    except Exception:
        return None
