import logging
import time
import warnings
from typing import Optional
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
# yfinance >=1.3 uses curl_cffi internally for browser impersonation —
# do NOT pass a requests.Session; let yfinance handle its own session.

_cache: dict = {}
_cache_ttl = 60  # seconds


def _cached(key: str, ttl: int = _cache_ttl):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < ttl:
        return entry["data"]
    return None


def _store(key: str, data) -> None:
    _cache[key] = {"data": data, "ts": time.time()}


def fetch_ticker_snapshot(symbol: str) -> Optional[dict]:
    cache_key = f"snap_{symbol}"
    cached = _cached(cache_key, ttl=60)
    if cached:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info
        hist = ticker.history(period="60d", interval="1d", auto_adjust=True)
        if hist.empty:
            print(f"[fetch] {symbol}: empty 60d history — skipping")
            return None

        avg_vol = int(hist["Volume"].tail(20).mean())
        raw_price = float(fi.get("lastPrice") or hist["Close"].iloc[-1])
        raw_prev  = float(fi.get("previousClose") or hist["Close"].iloc[-2])
        result = {
            "symbol":     symbol,
            "price":      raw_price,   # full precision — avoids rounding micro-prices to 0
            "prev_close": raw_prev,
            "volume":     int(fi.get("lastVolume") or hist["Volume"].iloc[-1]),
            "avg_volume": avg_vol,
            "hist":       hist,
        }
        result["change_pct"] = round(
            (raw_price - raw_prev) / raw_prev * 100, 2
        ) if raw_prev else 0.0
        _store(cache_key, result)
        return result
    except Exception as e:
        print(f"[fetch] {symbol}: exception — {e}")
        return None


def fetch_history(symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
    cache_key = f"hist_{symbol}_{period}"
    cached = _cached(cache_key, ttl=3600)
    if cached is not None:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval="1d", auto_adjust=True)
        if hist.empty:
            print(f"[fetch_hist] {symbol}: empty {period} history")
            return None
        _store(cache_key, hist)
        return hist
    except Exception as e:
        print(f"[fetch_hist] {symbol}: exception — {e}")
        return None


def fetch_multiple_snapshots(symbols: list[str]) -> dict[str, dict]:
    results = {}
    for sym in symbols:
        snap = fetch_ticker_snapshot(sym)
        if snap:
            results[sym] = snap
        else:
            print(f"[fetch_multi] {sym}: returned None — skipping")
        time.sleep(0.1)  # avoid rate limiting
    return results


def fetch_calendar(symbol: str) -> Optional[dict]:
    cache_key = f"cal_{symbol}"
    cached = _cached(cache_key, ttl=3600 * 4)
    if cached is not None:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        cal = ticker.calendar
        if cal is None or not isinstance(cal, dict):
            return None
        _store(cache_key, cal)
        return cal
    except Exception:
        return None


def fetch_earnings_history(symbol: str) -> Optional[pd.DataFrame]:
    cache_key = f"earndates_{symbol}"
    cached = _cached(cache_key, ttl=3600 * 6)
    if cached is not None:
        return cached

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.earnings_dates
        if df is None or df.empty:
            return None
        _store(cache_key, df)
        return df
    except Exception:
        return None
