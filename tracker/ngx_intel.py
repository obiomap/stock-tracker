"""
NGX (Nigerian Exchange) and African market intelligence:
  - USD/NGN spot rate via yfinance
  - NGX market hours (WAT = UTC+1, 10:00–14:30)
  - NGX sector context (breadth, top movers)
  - Low-liquidity confidence adjustment for LSE-listed African stocks
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional

_CACHE: dict = {}

_WAT        = timezone(timedelta(hours=1))   # West Africa Time = UTC+1
_NGX_OPEN   = (10, 0)    # 10:00 WAT
_NGX_CLOSE  = (14, 30)   # 14:30 WAT


def fetch_usdngn() -> dict:
    """USD/NGN spot rate via yfinance USDNGN=X. Cached 5 min."""
    key = "usdngn"
    e = _CACHE.get(key)
    if e and time.time() - e["ts"] < 300:
        return e["data"]
    result: dict = {"rate": None, "change_pct": None}
    try:
        import yfinance as yf
        fi   = yf.Ticker("USDNGN=X").fast_info
        rate = float(getattr(fi, "last_price", 0) or 0)
        prev = float(getattr(fi, "previous_close", 0) or 0)
        if rate > 0:
            chg = round((rate - prev) / prev * 100, 3) if prev > 0 else None
            result = {"rate": round(rate, 2), "change_pct": chg}
    except Exception:
        pass
    _CACHE[key] = {"data": result, "ts": time.time()}
    return result


def ngx_market_status() -> dict:
    """Is the NGX currently open? Minutes to open/close. Local WAT time string."""
    now_wat  = datetime.now(_WAT)
    weekday  = now_wat.weekday()   # 0=Mon, 6=Sun
    weekend  = weekday >= 5
    open_t   = now_wat.replace(hour=_NGX_OPEN[0],  minute=_NGX_OPEN[1],  second=0, microsecond=0)
    close_t  = now_wat.replace(hour=_NGX_CLOSE[0], minute=_NGX_CLOSE[1], second=0, microsecond=0)
    is_open  = (not weekend) and (open_t <= now_wat <= close_t)

    if is_open:
        mins_to_close = int((close_t - now_wat).total_seconds() / 60)
        return {"is_open": True,  "mins_to_close": mins_to_close, "mins_to_open": None,
                "local_time": now_wat.strftime("%H:%M WAT"), "session": "open"}
    else:
        if not weekend and now_wat < open_t:
            mins_to_open = int((open_t - now_wat).total_seconds() / 60)
        else:
            days_ahead = (7 - weekday) % 7 or 7  # next Monday
            next_open  = (now_wat + timedelta(days=days_ahead)).replace(
                hour=_NGX_OPEN[0], minute=_NGX_OPEN[1], second=0, microsecond=0)
            mins_to_open = int((next_open - now_wat).total_seconds() / 60)
        session = "weekend" if weekend else ("pre-market" if now_wat < open_t else "after-hours")
        return {"is_open": False, "mins_to_close": None, "mins_to_open": mins_to_open,
                "local_time": now_wat.strftime("%H:%M WAT"), "session": session}


def compute_ngx_context(ngx_stocks: list[dict]) -> dict:
    """Breadth, avg change, top 3 gainers/losers for tracked NGX/LSE-listed stocks."""
    empty = {"breadth_pct": 0, "breadth_above": 0, "breadth_total": 0,
             "avg_change": 0.0, "top_gainers": [], "top_losers": []}
    if not ngx_stocks:
        return empty

    with_price = [s for s in ngx_stocks if s.get("price")]
    if not with_price:
        return empty

    above  = sum(1 for s in with_price if s.get("ma50") and s["price"] > s["ma50"])
    total  = len(with_price)
    breadth_pct = round(above / total * 100, 1) if total else 0.0

    chgs       = [s.get("change_pct") or 0.0 for s in with_price]
    avg_change = round(sum(chgs) / len(chgs), 2) if chgs else 0.0

    ranked     = sorted(with_price, key=lambda s: s.get("change_pct") or 0.0)
    top_losers  = [{"symbol": s["symbol"], "change_pct": round(s.get("change_pct") or 0, 2)}
                   for s in ranked[:3]]
    top_gainers = [{"symbol": s["symbol"], "change_pct": round(s.get("change_pct") or 0, 2)}
                   for s in ranked[-3:][::-1]]

    return {"breadth_pct": breadth_pct, "breadth_above": above, "breadth_total": total,
            "avg_change": avg_change, "top_gainers": top_gainers, "top_losers": top_losers}


def ngx_liquidity_adjust(confidence: float, symbol: str) -> float:
    """
    Apply -12% confidence for LSE-listed African stocks (.L suffix).
    They have wider spreads and thinner order books than US-listed equities.
    """
    if symbol.endswith(".L"):
        return confidence * 0.88
    return confidence
