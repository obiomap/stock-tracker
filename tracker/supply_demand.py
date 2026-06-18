"""
Supply & demand intelligence:
  - Volume profile zones (demand / supply price levels, Point of Control)
  - Options OI levels (call wall, put wall, max pain)
  - Bid/ask spread & liquidity tier
"""

import time
from typing import Optional
import numpy as np
import pandas as pd

_CACHE: dict = {}


# ── Volume profile ─────────────────────────────────────────────────────────────

def volume_zones(hist: pd.DataFrame, current_price: float,
                 n_bins: int = 24, n_zones: int = 3) -> dict:
    """
    Bucket 2y daily history into price bins and sum volume per bucket.
    Returns the highest-volume zones below price (demand / support) and
    above price (supply / resistance), plus the Point of Control (POC).
    """
    if hist is None or len(hist) < 30 or not current_price:
        return {"demand": [], "supply": [], "poc": None}
    try:
        df = hist[["Close", "Volume"]].dropna().copy()
        if len(df) < 20:
            return {"demand": [], "supply": [], "poc": None}

        lo, hi = float(df["Close"].min()), float(df["Close"].max())
        if lo >= hi:
            return {"demand": [], "supply": [], "poc": None}

        bins   = np.linspace(lo, hi, n_bins + 1)
        mids   = (bins[:-1] + bins[1:]) / 2
        labels = list(range(n_bins))
        df["bin"] = pd.cut(df["Close"], bins=bins, labels=labels, include_lowest=True)
        vol_by_bin = df.groupby("bin", observed=True)["Volume"].sum()

        zones_all = [
            {"price": round(mids[i], 4), "volume": int(vol_by_bin.get(i, 0))}
            for i in range(n_bins)
        ]
        zones_all.sort(key=lambda x: x["volume"], reverse=True)

        poc = round(zones_all[0]["price"], 4) if zones_all else None

        demand = sorted(
            [z for z in zones_all if z["price"] < current_price * 0.999][:n_zones],
            key=lambda x: x["price"], reverse=True,   # nearest first
        )
        supply = sorted(
            [z for z in zones_all if z["price"] > current_price * 1.001][:n_zones],
            key=lambda x: x["price"],                  # nearest first
        )
        return {"demand": demand, "supply": supply, "poc": poc}
    except Exception:
        return {"demand": [], "supply": [], "poc": None}


# ── Options OI levels ──────────────────────────────────────────────────────────

def options_oi_levels(chain: Optional[dict]) -> dict:
    """
    From an option chain dict {calls: DataFrame, puts: DataFrame} compute:
      call_wall  — strike with peak call open interest (resistance)
      put_wall   — strike with peak put open interest  (support)
      max_pain   — strike minimising total intrinsic-value loss for all open interest
    """
    empty = {"call_wall": None, "put_wall": None, "max_pain": None}
    if not chain:
        return empty
    try:
        calls = chain.get("calls")
        puts  = chain.get("puts")
        call_wall = put_wall = max_pain = None

        if calls is not None and not calls.empty and "openInterest" in calls.columns:
            calls_c = calls.copy()
            calls_c["openInterest"] = pd.to_numeric(calls_c["openInterest"], errors="coerce").fillna(0)
            idx = calls_c["openInterest"].idxmax()
            call_wall = round(float(calls_c.loc[idx, "strike"]), 2)

        if puts is not None and not puts.empty and "openInterest" in puts.columns:
            puts_c = puts.copy()
            puts_c["openInterest"] = pd.to_numeric(puts_c["openInterest"], errors="coerce").fillna(0)
            idx = puts_c["openInterest"].idxmax()
            put_wall = round(float(puts_c.loc[idx, "strike"]), 2)

        # Max pain (vectorised)
        if (calls is not None and not calls.empty and
                puts is not None and not puts.empty):
            calls_c = calls_c if "openInterest" in calls.columns else calls.copy()
            puts_c  = puts_c  if "openInterest" in puts.columns  else puts.copy()
            strikes  = np.array(sorted(
                set(calls_c["strike"].tolist() + puts_c["strike"].tolist())
            ), dtype=float)
            c_strikes = calls_c["strike"].values.astype(float)
            c_oi      = pd.to_numeric(calls_c["openInterest"], errors="coerce").fillna(0).values
            p_strikes = puts_c["strike"].values.astype(float)
            p_oi      = pd.to_numeric(puts_c["openInterest"], errors="coerce").fillna(0).values

            c_pain = np.sum(
                np.maximum(0, strikes[:, None] - c_strikes[None, :]) * c_oi[None, :], axis=1
            )
            p_pain = np.sum(
                np.maximum(0, p_strikes[None, :] - strikes[:, None]) * p_oi[None, :], axis=1
            )
            max_pain = round(float(strikes[np.argmin(c_pain + p_pain)]), 2)

        return {"call_wall": call_wall, "put_wall": put_wall, "max_pain": max_pain}
    except Exception:
        return empty


# ── Bid/ask spread ─────────────────────────────────────────────────────────────

def bid_ask_spread(sym: str) -> dict:
    """
    Fetch live bid/ask via yfinance fast_info. Cached 60 s.
    Returns bid, ask, spread_pct, and a liquidity tier label.
    """
    key = f"ba_{sym}"
    entry = _CACHE.get(key)
    if entry and time.time() - entry["ts"] < 60:
        return entry["data"]

    result: dict = {"bid": None, "ask": None, "spread_pct": None, "liquidity": "unknown"}
    try:
        import yfinance as yf
        fi  = yf.Ticker(sym).fast_info
        bid = float(getattr(fi, "bid", 0) or 0)
        ask = float(getattr(fi, "ask", 0) or 0)
        if bid > 0 and ask > 0 and ask >= bid:
            mid = (bid + ask) / 2
            sp  = round((ask - bid) / mid * 100, 3)
            liq = ("excellent" if sp < 0.05 else
                   "good"      if sp < 0.15 else
                   "moderate"  if sp < 0.50 else "thin")
            result = {"bid": round(bid, 4), "ask": round(ask, 4),
                      "spread_pct": sp, "liquidity": liq}
    except Exception:
        pass
    _CACHE[key] = {"data": result, "ts": time.time()}
    return result
