"""
Alpaca brokerage integration — paper & live trading.

Configure via environment variables (set in Railway or .env):
  ALPACA_API_KEY    — Alpaca API key ID
  ALPACA_API_SECRET — Alpaca API secret
  ALPACA_PAPER      — "true" (default) for paper trading, "false" for live

WARNING: setting ALPACA_PAPER=false submits real orders with real money.
"""

import os
import threading
import time
from datetime import datetime
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


# ── Broker read cache (Flask handlers never block on Alpaca REST) ─────────────
#
# Historical incident: on 2026-07-13 the dashboard route did synchronous
# get_positions()+get_account() calls per request. Alpaca connectivity glitched,
# every request blocked ~30-300s until timeout, and Flask's worker pool
# saturated — the whole site went unresponsive. Now a background thread does
# the blocking calls and Flask handlers only read from the in-memory cache.
_broker_cache: dict = {
    "positions":   [],
    "account":     None,
    "orders_open": [],
    "last_ok":     0.0,
    "last_err":    "",
}
_broker_refresh_lock = threading.Lock()
_broker_refresher_started = False
_BROKER_REFRESH_S = 15  # background poll interval


def _ensure_broker_refresher() -> None:
    """Idempotently start the background refresher thread on first cached read."""
    global _broker_refresher_started
    if _broker_refresher_started or not is_configured():
        return
    with _broker_refresh_lock:
        if _broker_refresher_started:
            return
        _broker_refresher_started = True

        def _loop() -> None:
            while True:
                try:
                    _broker_cache["positions"]   = _fetch_positions()
                    _broker_cache["account"]     = _fetch_account()
                    _broker_cache["orders_open"] = _fetch_orders("open")
                    _broker_cache["last_ok"]     = time.time()
                    _broker_cache["last_err"]    = ""
                except Exception as e:
                    _broker_cache["last_err"] = str(e)
                time.sleep(_BROKER_REFRESH_S)

        threading.Thread(target=_loop, daemon=True, name="broker-refresher").start()


def invalidate_broker_cache() -> None:
    """Kick off an immediate refresh (best-effort, non-blocking) after a mutation.
    Runs the refetches in a one-shot thread so the request thread returns fast.
    """
    if not is_configured():
        return

    def _refresh_once() -> None:
        try:
            _broker_cache["positions"]   = _fetch_positions()
            _broker_cache["orders_open"] = _fetch_orders("open")
            _broker_cache["account"]     = _fetch_account()
            _broker_cache["last_ok"]     = time.time()
        except Exception as e:
            _broker_cache["last_err"] = str(e)

    threading.Thread(target=_refresh_once, daemon=True, name="broker-invalidate").start()


def start_broker_refresher() -> None:
    """Public entry: warm the cache at startup instead of on first request."""
    _ensure_broker_refresher()


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
        invalidate_broker_cache()
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


def _fetch_positions() -> list[dict]:
    """Live REST call — blocks until Alpaca responds. Use get_positions() from Flask handlers."""
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


def _fetch_account() -> Optional[dict]:
    """Live REST call — blocks until Alpaca responds. Use get_account() from Flask handlers."""
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


def get_positions() -> list[dict]:
    """Cached; non-blocking. Refreshed by the broker refresher thread."""
    _ensure_broker_refresher()
    return list(_broker_cache["positions"])


def get_account() -> Optional[dict]:
    """Cached; non-blocking. Refreshed by the broker refresher thread."""
    _ensure_broker_refresher()
    return _broker_cache["account"]


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
        invalidate_broker_cache()
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
        invalidate_broker_cache()
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
        invalidate_broker_cache()
        return {"ok": True, "id": str(order.id), "status": str(order.status),
                "symbol": order.symbol, "qty": float(order.qty or qty),
                "side": side.upper(), "paper": is_paper(), "type": "trailing_stop",
                "trail_percent": trail_percent, "trail_price": trail_price}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _fetch_orders(status: str = "open") -> list[dict]:
    """Live REST call — blocks until Alpaca responds. Use get_orders() from Flask handlers."""
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


def get_orders(status: str = "open") -> list[dict]:
    """Cached; non-blocking. status = 'open' | 'all' | 'closed'.
    Only 'open' is prefetched by the refresher; 'all'/'closed' fall back to a live call.
    """
    _ensure_broker_refresher()
    if status == "open":
        return list(_broker_cache["orders_open"])
    return _fetch_orders(status)


def cancel_order(order_id: str) -> dict:
    """Cancel an order by ID. Returns {ok, id}."""
    if not is_configured():
        return {"ok": False, "error": "Alpaca credentials not configured"}
    try:
        _client().cancel_order_by_id(order_id)
        invalidate_broker_cache()
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

_stream_state: dict = {
    "fills":       [],
    "running":     False,
    "errors":      0,
    "reconnects":  0,
    "last_error":  "",
    "started_at":  0.0,
}

_STREAM_BACKOFF_START_S = 2.0
_STREAM_BACKOFF_MAX_S   = 300.0
_STREAM_STABLE_S        = 60.0   # if run() stays alive >= this, reset backoff
_ALPACA_LOG_WINDOW_S    = 60.0   # coalesce identical log records within this window


class _RateLimitFilter:
    """Logging filter that suppresses repeats of the same message within a window.

    The Alpaca SDK's trading-stream reconnect loop calls log.exception() on
    every failed connect. During a network outage that produces a flood of
    identical multi-line tracebacks in the deploy log. This filter keeps the
    first occurrence per window and drops the rest, annotating the next
    surviving record with the suppressed count.
    """
    def __init__(self, window_s: float) -> None:
        self.window_s   = window_s
        self._last_ts:   dict = {}
        self._suppressed: dict = {}

    def filter(self, record) -> bool:  # noqa: A003 — logging Filter API
        key = f"{record.levelno}|{record.name}|{str(record.msg)[:120]}"
        now = time.time()
        last = self._last_ts.get(key, 0.0)
        if now - last < self.window_s:
            self._suppressed[key] = self._suppressed.get(key, 0) + 1
            return False
        n = self._suppressed.pop(key, 0)
        if n:
            record.msg = f"{record.msg}  (+{n} similar suppressed in last {int(self.window_s)}s)"
        self._last_ts[key] = now
        return True


_alpaca_logging_configured = False


def _configure_alpaca_logging() -> None:
    """Attach a rate-limit filter to the alpaca stream logger to suppress flood.

    log.exception() and log.warning() from alpaca.trading.stream._run_forever
    fire on every reconnect attempt during an Alpaca outage — this collapses
    identical messages within the window.
    """
    global _alpaca_logging_configured
    if _alpaca_logging_configured:
        return
    _alpaca_logging_configured = True
    import logging as _logging
    flt = _RateLimitFilter(window_s=_ALPACA_LOG_WINDOW_S)
    for name in ("alpaca", "alpaca.trading.stream", "websockets"):
        _logging.getLogger(name).addFilter(flt)


def get_recent_fills() -> list[dict]:
    return list(_stream_state["fills"])


def get_stream_state() -> dict:
    """Snapshot of the trade-stream supervisor state (for debug/observability)."""
    return {k: v for k, v in _stream_state.items() if k != "fills"}


def start_trade_stream() -> None:
    """Start Alpaca TradingStream in a background daemon thread with supervisor.

    - The SDK's ts.run() has its own internal reconnect loop; if it ever exits
      or crashes fully, the supervisor restarts it with exponential backoff
      (2s → 4s → ... → 300s cap). Backoff resets after ~60s of stable running.
    - Alpaca SDK log noise from failed reconnects is rate-limited to at most
      one identical record per _ALPACA_LOG_WINDOW_S window.
    - Fill events trigger invalidate_broker_cache() so positions/account
      reflect the fill within ~1s instead of waiting for the 15s refresher.
    """
    if not is_configured() or _stream_state["running"]:
        return

    _configure_alpaca_logging()

    def _run() -> None:
        backoff = _STREAM_BACKOFF_START_S

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
                    invalidate_broker_cache()
            except Exception:
                pass

        while True:
            try:
                from alpaca.trading.stream import TradingStream
                ts = TradingStream(
                    os.environ["ALPACA_API_KEY"],
                    os.environ["ALPACA_API_SECRET"],
                    paper=is_paper(),
                )
                ts.subscribe_trade_updates(_on_update)

                _stream_state["running"]    = True
                _stream_state["started_at"] = time.time()
                ts.run()   # blocks; SDK's internal loop handles most retries
                # If ts.run() returns, the internal loop exited — supervise a restart
                _stream_state["running"] = False
                _stream_state["reconnects"] += 1
            except Exception as e:
                _stream_state["running"] = False
                _stream_state["errors"] += 1
                _stream_state["last_error"] = f"{type(e).__name__}: {e}"
                # Rate-limited via our filter (this goes through our own logger)
                import logging as _logging
                _logging.getLogger("alpaca.trading.stream").error(
                    "supervisor: trade stream run() raised %s: %s",
                    type(e).__name__, e,
                )

            # Reset backoff if the last run held together for a while
            uptime = time.time() - _stream_state.get("started_at", 0.0)
            if uptime >= _STREAM_STABLE_S:
                backoff = _STREAM_BACKOFF_START_S
            time.sleep(backoff)
            backoff = min(backoff * 2, _STREAM_BACKOFF_MAX_S)

    threading.Thread(target=_run, daemon=True, name="broker-trade-stream").start()


# ── Options trading ────────────────────────────────────────────────────────────

def _build_occ_symbol(underlying: str, expiry: str, strike: float, opt_type: str) -> str:
    """Return OCC option symbol, e.g. NVDA260626C00850000."""
    dt = datetime.strptime(expiry, "%Y-%m-%d")
    type_char = "C" if opt_type.upper() == "CALL" else "P"
    strike_int = int(round(strike * 1000))
    return f"{underlying.upper()}{dt.strftime('%y%m%d')}{type_char}{strike_int:08d}"


def get_option_quote(underlying: str, expiry: str, strike: float, opt_type: str) -> dict:
    """Fetch bid/ask for an option contract via yfinance. Returns {ok, bid, ask, last, symbol}."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(underlying)
        chain = ticker.option_chain(expiry)
        df = chain.calls if opt_type.upper() == "CALL" else chain.puts
        exact = df[df["strike"] == float(strike)]
        row = exact if not exact.empty else df.iloc[(df["strike"] - float(strike)).abs().argsort()[:1]]
        if row.empty:
            return {"ok": False, "error": "No contract found for that strike"}
        r = row.iloc[0]
        return {
            "ok":     True,
            "bid":    float(r.get("bid", 0) or 0),
            "ask":    float(r.get("ask", 0) or 0),
            "last":   float(r.get("lastPrice", 0) or 0),
            "symbol": _build_occ_symbol(underlying, expiry, strike, opt_type),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def place_option_limit_order(underlying: str, expiry: str, strike: float,
                              opt_type: str, qty: int, limit_price: float) -> dict:
    """Buy an option contract at a DAY limit price."""
    if not is_configured():
        return {"ok": False, "error": "Alpaca credentials not configured"}
    if qty <= 0:
        return {"ok": False, "error": "Quantity must be > 0"}
    if limit_price <= 0:
        return {"ok": False, "error": "Limit price must be > 0"}
    try:
        occ_sym = _build_occ_symbol(underlying, expiry, strike, opt_type)
        from alpaca.trading.requests import LimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        req = LimitOrderRequest(
            symbol=occ_sym,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
        )
        order = _client().submit_order(req)
        invalidate_broker_cache()
        return {
            "ok":          True,
            "id":          str(order.id),
            "status":      str(order.status),
            "symbol":      occ_sym,
            "underlying":  underlying,
            "expiry":      expiry,
            "strike":      strike,
            "opt_type":    opt_type.upper(),
            "qty":         int(qty),
            "limit_price": limit_price,
            "paper":       is_paper(),
            "type":        "option_limit",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def close_option_position(occ_symbol: str, qty: int, current_bid: float) -> dict:
    """Sell to close an option position.  Uses a limit at bid (or market if bid=0)."""
    if not is_configured():
        return {"ok": False, "error": "Alpaca credentials not configured"}
    if qty <= 0:
        return {"ok": False, "error": "Quantity must be > 0"}
    try:
        from alpaca.trading.enums import OrderSide, TimeInForce
        if current_bid and current_bid > 0:
            from alpaca.trading.requests import LimitOrderRequest
            req = LimitOrderRequest(
                symbol=occ_symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
                limit_price=round(current_bid, 2),
            )
        else:
            from alpaca.trading.requests import MarketOrderRequest
            req = MarketOrderRequest(
                symbol=occ_symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
        order = _client().submit_order(req)
        invalidate_broker_cache()
        return {
            "ok":     True,
            "id":     str(order.id),
            "status": str(order.status),
            "symbol": occ_symbol,
            "qty":    int(qty),
            "paper":  is_paper(),
            "type":   "option_close",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
