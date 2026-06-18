"""
Order flow intelligence using intraday 5-minute candles:
  - Volume spike detection (≥3× rolling average)
  - Sell-off detector (bearish candles + price below VWAP)
  - Buy/sell pressure ratio (up-tick vs down-tick volume)
  - Price velocity alert (≥1% single-candle move)
"""

import time
from typing import Optional

import numpy as np
import pandas as pd

_CACHE: dict = {}
_TTL = 300  # 5-min cache for intraday data


def _fetch_5min(sym: str) -> Optional[pd.DataFrame]:
    """Fetch 1 day of 5-min OHLCV candles. Cached 5 min."""
    key = f"5m_{sym}"
    e = _CACHE.get(key)
    if e and time.time() - e["ts"] < _TTL:
        return e["data"]
    result = None
    try:
        import yfinance as yf
        df = yf.download(sym, period="1d", interval="5m", progress=False, auto_adjust=True)
        if df is not None and not df.empty and len(df) >= 4:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            result = df.copy()
    except Exception:
        pass
    _CACHE[key] = {"data": result, "ts": time.time()}
    return result


def _vwap(df: pd.DataFrame) -> pd.Series:
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    cum_vol = df["Volume"].cumsum().replace(0, float("nan"))
    return (typical * df["Volume"]).cumsum() / cum_vol


def detect_volume_spike(df: Optional[pd.DataFrame], threshold: float = 3.0) -> dict:
    """Largest volume spike over last 20 candles vs 20-candle rolling average."""
    empty = {"spike": False, "ratio": None, "time": None, "price": None}
    try:
        if df is None or len(df) < 5:
            return empty
        rolling_avg = df["Volume"].rolling(20, min_periods=3).mean()
        ratios = df["Volume"] / rolling_avg.replace(0, float("nan"))
        recent = ratios.tail(20).dropna()
        if recent.empty:
            return empty
        max_idx = recent.idxmax()
        max_ratio = float(recent[max_idx])
        if max_ratio >= threshold:
            price = round(float(df.loc[max_idx, "Close"]), 2)
            ts_str = str(max_idx)[:16]
            return {"spike": True, "ratio": round(max_ratio, 1), "time": ts_str, "price": price}
        return empty
    except Exception:
        return empty


def detect_selloff(df: Optional[pd.DataFrame]) -> dict:
    """Sell-off = last 3 candles: ≥2 bearish, net drop >0.5%, price below VWAP."""
    empty = {"selloff": False, "drop_pct": None, "below_vwap": False}
    try:
        if df is None or len(df) < 6:
            return empty
        recent = df.tail(6).copy()
        vwap_ser = _vwap(df).reindex(recent.index)
        vwap_now = float(vwap_ser.iloc[-1]) if not pd.isna(vwap_ser.iloc[-1]) else None

        last3 = recent.tail(3)
        bearish = sum(1 for _, row in last3.iterrows()
                      if float(row["Close"]) < float(row["Open"]))
        first_open = float(last3.iloc[0]["Open"])
        last_close = float(last3.iloc[-1]["Close"])
        drop_pct = (last_close - first_open) / abs(first_open) * 100 if first_open else 0
        below_vwap = bool(vwap_now and last_close < vwap_now * 0.999)

        if bearish >= 2 and drop_pct < -0.5 and below_vwap:
            return {"selloff": True, "drop_pct": round(drop_pct, 2), "below_vwap": below_vwap}
        return empty
    except Exception:
        return empty


def buy_sell_pressure(df: Optional[pd.DataFrame]) -> dict:
    """Up-tick vs down-tick volume ratio over last 20 candles."""
    empty = {"buy_ratio": None, "label": "neutral", "buy_vol": None, "sell_vol": None}
    try:
        if df is None or len(df) < 5:
            return empty
        recent = df.tail(20).copy()
        body = recent["Close"] - recent["Open"]
        buy_vol  = float(recent["Volume"].where(body > 0, 0).sum())
        sell_vol = float(recent["Volume"].where(body < 0, 0).sum())
        total = buy_vol + sell_vol
        if total <= 0:
            return empty
        ratio = round(buy_vol / total, 3)
        label = ("strong buy"  if ratio > 0.65 else
                 "buy"         if ratio > 0.55 else
                 "strong sell" if ratio < 0.35 else
                 "sell"        if ratio < 0.45 else "neutral")
        return {"buy_ratio": ratio, "label": label,
                "buy_vol": int(buy_vol), "sell_vol": int(sell_vol)}
    except Exception:
        return empty


def price_velocity(df: Optional[pd.DataFrame]) -> dict:
    """Largest single-candle % move in last 10 candles. Alert if ≥1%."""
    empty = {"alert": False, "max_pct": None, "direction": None}
    try:
        if df is None or len(df) < 3:
            return empty
        recent = df.tail(10).copy()
        opens = recent["Open"].replace(0, float("nan"))
        pct = ((recent["Close"] - opens) / opens * 100).dropna()
        if pct.empty:
            return empty
        idx = pct.abs().idxmax()
        val = round(float(pct[idx]), 2)
        return {"alert": abs(val) >= 1.0, "max_pct": val,
                "direction": "up" if val > 0 else "down"}
    except Exception:
        return empty


def analyze(sym: str) -> dict:
    """Run all order-flow checks for a symbol (fetches 5-min data, cached 5 min)."""
    df = _fetch_5min(sym)
    return {
        "symbol":        sym,
        "volume_spike":  detect_volume_spike(df),
        "selloff":       detect_selloff(df),
        "pressure":      buy_sell_pressure(df),
        "velocity":      price_velocity(df),
        "ts":            time.time(),
    }
