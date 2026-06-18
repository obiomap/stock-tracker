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


def place_limit_order(symbol: str, qty: float, side: str, limit_price: float) -> dict:
    """Submit a DAY limit order. Returns {ok, id, status, symbol, qty, side, paper}."""
    if not is_configured():
        return {"ok": False, "error": "Alpaca credentials not configured"}
    if qty <= 0:
        return {"ok": False, "error": "Quantity must be > 0"}
    if limit_price <= 0:
        return {"ok": False, "error": "Limit price must be > 0"}
    try:
        from alpaca.trading.requests import LimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        req = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
        )
        order = _client().submit_order(req)
        return {"ok": True, "id": str(order.id), "status": str(order.status),
                "symbol": order.symbol, "qty": float(order.qty or qty),
                "side": side.upper(), "paper": is_paper(), "type": "limit",
                "limit_price": limit_price}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def place_stop_limit_order(symbol: str, qty: float, side: str,
                           limit_price: float, stop_price: float) -> dict:
    """Submit a DAY stop-limit order."""
    if not is_configured():
        return {"ok": False, "error": "Alpaca credentials not configured"}
    if qty <= 0:
        return {"ok": False, "error": "Quantity must be > 0"}
    if limit_price <= 0 or stop_price <= 0:
        return {"ok": False, "error": "Prices must be > 0"}
    try:
        from alpaca.trading.requests import StopLimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        req = StopLimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
            stop_price=stop_price,
        )
        order = _client().submit_order(req)
        return {"ok": True, "id": str(order.id), "status": str(order.status),
                "symbol": order.symbol, "qty": float(order.qty or qty),
                "side": side.upper(), "paper": is_paper(), "type": "stop_limit",
                "limit_price": limit_price, "stop_price": stop_price}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def place_trailing_stop_order(symbol: str, qty: float, side: str,
                              trail_percent: Optional[float] = None,
                              trail_price: Optional[float] = None) -> dict:
    """
    Submit a DAY trailing stop order.
    Provide either trail_percent (e.g. 2.0 for 2%) or trail_price (e.g. 1.50 for $1.50).
    """
    if not is_configured():
        return {"ok": False, "error": "Alpaca credentials not configured"}
    if qty <= 0:
        return {"ok": False, "error": "Quantity must be > 0"}
    if not trail_percent and not trail_price:
        return {"ok": False, "error": "Provide trail_percent or trail_price"}
    try:
        from alpaca.trading.requests import TrailingStopOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        kwargs: dict = dict(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        if trail_percent:
            kwargs["trail_percent"] = trail_percent
        else:
            kwargs["trail_price"] = trail_price
        order = _client().submit_order(TrailingStopOrderRequest(**kwargs))
        return {"ok": True, "id": str(order.id), "status": str(order.status),
                "symbol": order.symbol, "qty": float(order.qty or qty),
                "side": side.upper(), "paper": is_paper(), "type": "trailing_stop",
                "trail_percent": trail_percent, "trail_price": trail_price}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_orders(status: str = "open") -> list[dict]:
    """Return open/all orders. status = 'open' | 'all' | 'closed'."""
    if not is_configured():
        return []
    try:
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus
        status_map = {
            "open":   QueryOrderStatus.OPEN,
            "closed": QueryOrderStatus.CLOSED,
            "all":    QueryOrderStatus.ALL,
        }
        req = GetOrdersRequest(status=status_map.get(status, QueryOrderStatus.OPEN))
        orders = _client().get_orders(filter=req)
        result = []
        for o in orders:
            result.append({
                "id":          str(o.id),
                "symbol":      o.symbol,
                "side":        str(o.side).split(".")[-1].upper(),
                "type":        str(o.type).split(".")[-1].lower(),
                "qty":         float(o.qty or 0),
                "filled_qty":  float(o.filled_qty or 0),
                "status":      str(o.status).split(".")[-1].lower(),
                "limit_price": float(o.limit_price) if o.limit_price else None,
                "stop_price":  float(o.stop_price) if o.stop_price else None,
                "created_at":  str(o.created_at)[:19] if o.created_at else "",
                "paper":       is_paper(),
            })
        return result
    except Exception:
        return []


def cancel_order(order_id: str) -> dict:
    """Cancel an order by ID. Returns {ok, id}."""
    if not is_configured():
        return {"ok": False, "error": "Alpaca credentials not configured"}
    try:
        _client().cancel_order_by_id(order_id)
        return {"ok": True, "id": order_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def auto_execute_signal(symbol: str, signal: str, confidence: float,
                        price: float, threshold: float = 0.85,
                        qty: float = 1.0) -> dict:
    """
    Auto-submit a paper market order if signal is BULLISH/BEARISH and
    confidence >= threshold. Always uses paper mode for safety.
    """
    if not is_configured():
        return {"ok": False, "skipped": True, "reason": "not configured"}
    if confidence < threshold:
        return {"ok": False, "skipped": True,
                "reason": f"confidence {confidence:.0%} < threshold {threshold:.0%}"}
    if signal == "BULLISH":
        r = place_order(symbol, qty, "BUY")
        r["auto"] = True
        return r
    if signal == "BEARISH":
        r = place_order(symbol, qty, "SELL")
        r["auto"] = True
        return r
    return {"ok": False, "skipped": True, "reason": "neutral signal"}


# ── Real-time trade stream (fills via Alpaca websocket) ────────────────────────

_stream_state: dict = {"fills": [], "running": False, "errors": 0}


def get_recent_fills() -> list[dict]:
    return list(_stream_state["fills"])


def start_trade_stream() -> None:
    """Start Alpaca TradingStream in a background daemon thread to capture fills."""
    if not is_configured() or _stream_state["running"]:
        return
    import threading

    def _run() -> None:
        _stream_state["running"] = True
        try:
            from alpaca.trading.stream import TradingStream

            async def _on_update(data) -> None:
                try:
                    event = str(getattr(data, "event", "")).lower()
                    if event in ("fill", "partial_fill"):
                        order = getattr(data, "order", None)
                        fill = {
                            "ts":     str(getattr(data, "timestamp", ""))[:19],
                            "symbol": str(order.symbol) if order else "?",
                            "side":   str(order.side).upper() if order else "?",
                            "qty":    float(getattr(order, "filled_qty", 0) or 0),
                            "price":  float(getattr(data, "price", 0) or 0),
                            "event":  event,
                        }
                        _stream_state["fills"] = (_stream_state["fills"] + [fill])[-50:]
                except Exception:
                    pass

            ts = TradingStream(
                os.environ["ALPACA_API_KEY"],
                os.environ["ALPACA_API_SECRET"],
                paper=is_paper(),
            )
            ts.subscribe_trade_updates(_on_update)
            ts.run()
        except Exception as e:
            _stream_state["running"] = False
            _stream_state["errors"] += 1
            print(f"[broker] trade stream error: {e}", flush=True)

    threading.Thread(target=_run, daemon=True).start()
