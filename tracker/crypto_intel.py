"""
Crypto market intelligence:
  - Fear & Greed Index (alternative.me — free, no key)
  - BTC dominance (CoinGecko /global — free, no key)
  - BTC regime (MA20/MA50, mirrors SPX Pulse logic)
  - Per-coin 30-day BTC return correlation
"""

import time
from typing import Optional

import numpy as np
import pandas as pd

_CACHE: dict = {}
_TTL_HOUR = 3600


def fetch_fear_greed() -> dict:
    """Crypto Fear & Greed Index (0=extreme fear, 100=extreme greed). Cached 1 h."""
    key = "fear_greed"
    e = _CACHE.get(key)
    if e and time.time() - e["ts"] < _TTL_HOUR:
        return e["data"]
    result: dict = {"value": None, "label": "unknown", "trend": ""}
    try:
        import requests
        r = requests.get("https://api.alternative.me/fng/?limit=2", timeout=8)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                v     = int(data[0]["value"])
                label = data[0]["value_classification"]
                trend = ""
                if len(data) >= 2:
                    prev  = int(data[1]["value"])
                    trend = "improving" if v > prev else ("declining" if v < prev else "stable")
                result = {"value": v, "label": label, "trend": trend}
    except Exception:
        pass
    _CACHE[key] = {"data": result, "ts": time.time()}
    return result


def fetch_btc_dominance() -> dict:
    """BTC and ETH % of total crypto market cap from CoinGecko. Cached 1 h."""
    key = "btc_dom"
    e = _CACHE.get(key)
    if e and time.time() - e["ts"] < _TTL_HOUR:
        return e["data"]
    result: dict = {"btc": None, "eth": None}
    try:
        import requests
        r = requests.get(
            "https://api.coingecko.com/api/v3/global",
            timeout=8,
            headers={"Accept": "application/json"},
        )
        if r.status_code == 200:
            pcts = r.json().get("data", {}).get("market_cap_percentage", {})
            result = {
                "btc": round(float(pcts.get("btc") or 0), 1),
                "eth": round(float(pcts.get("eth") or 0), 1),
            }
    except Exception:
        pass
    _CACHE[key] = {"data": result, "ts": time.time()}
    return result


def compute_btc_regime(btc_hist: Optional[pd.DataFrame], btc_price: float) -> dict:
    """5-level BTC regime (strong bull / bull / neutral / bear / strong bear) via MA20/MA50."""
    empty = {"score": 0.0, "label": "neutral", "ma20": None, "ma50": None}
    if btc_hist is None or len(btc_hist) < 55 or not btc_price:
        return empty
    try:
        close = btc_hist["Close"].dropna()
        ma20 = float(close.rolling(20).mean().iloc[-1])
        ma50 = float(close.rolling(50).mean().iloc[-1])
        if not ma20 or not ma50:
            return empty

        d20 = (btc_price - ma20) / ma20
        d50 = (btc_price - ma50) / ma50
        if d20 > 0.01:
            score, label = (2.0, "strong bull") if d50 > 0.02 else (1.0, "bull")
        elif d20 < -0.01:
            score, label = (-2.0, "strong bear") if d50 < -0.02 else (-1.0, "bear")
        else:
            score, label = 0.0, "neutral"

        return {"score": score, "label": label,
                "ma20": round(ma20, 0), "ma50": round(ma50, 0)}
    except Exception:
        return empty


def btc_correlation(coin_hist: Optional[pd.DataFrame],
                    btc_hist: Optional[pd.DataFrame],
                    days: int = 30) -> Optional[float]:
    """30-day Pearson correlation of daily returns between a coin and BTC."""
    if coin_hist is None or btc_hist is None:
        return None
    try:
        coin_ret = coin_hist["Close"].dropna().pct_change().dropna().tail(days)
        btc_ret  = btc_hist["Close"].dropna().pct_change().dropna().tail(days)
        aligned  = pd.concat([coin_ret, btc_ret], axis=1).dropna()
        if len(aligned) < 10:
            return None
        corr = float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))
        return round(corr, 3) if not np.isnan(corr) else None
    except Exception:
        return None
