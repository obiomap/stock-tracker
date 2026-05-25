"""
Options intelligence: fetch option chains, score contracts, generate call/put recommendations.

Workflow:
  1. refresh_options() in main.py calls get_recommendations() for each high-signal stock.
  2. Recommendations are stored in the DB (options_recs table).
  3. web.py reads get_option_recs() and renders the Options Intelligence section.
"""

import time
from datetime import datetime
from typing import Optional
import pandas as pd
import yfinance as yf

_cache: dict = {}
_CACHE_TTL = 900  # 15 minutes — options prices change slowly

# Symbols that never have tradeable options (crypto, London-listed, most foreign ADRs)
NO_OPTIONS: frozenset = frozenset([
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "ADA-USD", "AVAX-USD",
    "TON-USD", "NEAR-USD", "APT21794-USD", "SUI20947-USD", "HBAR-USD", "XLM-USD",
    "ATOM-USD", "POL28321-USD", "ARB-USD", "OP-USD", "LINK-USD", "UNI7083-USD",
    "AAVE-USD", "MKR-USD", "LDO-USD", "CRV-USD", "GRT6719-USD", "RENDER-USD",
    "FET-USD", "SEI-USD", "TAO22974-USD", "TIA-USD", "WLD-USD", "JUP-USD", "ENA-USD",
    "ONDO-USD", "IMX10603-USD", "SAND-USD", "MANA-USD", "AXS-USD", "CHZ-USD",
    "INJ-USD", "RUNE-USD", "STX4847-USD", "ZEC-USD", "KAS-USD", "DOT-USD", "LTC-USD",
    "ALGO-USD", "ICP-USD", "VET-USD", "DOGE-USD", "SHIB-USD", "PEPE24478-USD",
    "WIF-USD", "BONK-USD", "FLOKI-USD",
    # London-listed (no US options market)
    "AAF.L", "SEPL.L",
    # Foreign ADRs with thin or no US options market
    "MTNOY", "NPSNY", "NTDOY", "BYDDY", "TCEHY",
    "LVMUY", "EADSY", "SIEGY", "VWAGY", "BMWYY",
    "NSRGY", "NSRGY", "MUFG",
])


def is_optionable(symbol: str, price: float) -> bool:
    """Return True if the symbol is likely to have a liquid US options market."""
    if symbol in NO_OPTIONS:
        return False
    if "-USD" in symbol or ".L" in symbol:
        return False
    if price < 5:          # sub-$5 options are usually illiquid
        return False
    return True


def fetch_option_chain(symbol: str) -> Optional[dict]:
    """
    Fetch the nearest 1-2 expiry dates (7-60 days out) for a symbol.
    Returns {"calls": DataFrame, "puts": DataFrame} or None on failure.
    """
    cache_key = f"opt_{symbol}"
    entry = _cache.get(cache_key)
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        return entry["data"]

    try:
        ticker  = yf.Ticker(symbol)
        expiries = ticker.options          # tuple of "YYYY-MM-DD" strings
        if not expiries:
            _cache[cache_key] = {"data": None, "ts": time.time()}
            return None

        # Pick expiries 7-60 days out (balance time-value vs. relevance)
        now    = datetime.now()
        target = []
        for exp in expiries:
            try:
                exp_dt = datetime.strptime(exp, "%Y-%m-%d")
            except ValueError:
                continue
            days = (exp_dt - now).days
            if 7 <= days <= 60:
                target.append(exp)
            if len(target) >= 2:
                break
        if not target:
            target = [expiries[0]]         # fall back to nearest expiry

        all_calls, all_puts = [], []
        for exp in target:
            try:
                chain = ticker.option_chain(exp)
                c = chain.calls.copy()
                p = chain.puts.copy()
                c["expiry"] = exp
                p["expiry"] = exp
                all_calls.append(c)
                all_puts.append(p)
            except Exception:
                continue

        if not all_calls and not all_puts:
            _cache[cache_key] = {"data": None, "ts": time.time()}
            return None

        result = {
            "calls": pd.concat(all_calls, ignore_index=True) if all_calls else pd.DataFrame(),
            "puts":  pd.concat(all_puts,  ignore_index=True) if all_puts  else pd.DataFrame(),
        }
        _cache[cache_key] = {"data": result, "ts": time.time()}
        return result

    except Exception:
        _cache[cache_key] = {"data": None, "ts": time.time()}
        return None


def _score_contract(row: dict, current_price: float, opt_type: str) -> float:
    """
    Score a single option contract 0-100.
    Higher = more attractive (liquid, well-placed strike, reasonable IV).
    """
    def _safe_float(v, default=0.0):
        try:
            f = float(v)
            return default if (f != f) else f  # NaN check: NaN != NaN
        except (TypeError, ValueError):
            return default

    def _safe_int(v, default=0):
        try:
            f = float(v)
            return default if (f != f) else int(f)
        except (TypeError, ValueError):
            return default

    strike = _safe_float(row.get("strike"))
    iv     = _safe_float(row.get("impliedVolatility"))
    oi     = _safe_int(row.get("openInterest"))
    vol    = _safe_int(row.get("volume"))
    bid    = _safe_float(row.get("bid"))
    ask    = _safe_float(row.get("ask"))

    if not strike or not current_price:
        return 0.0

    score = 0.0

    # ── Moneyness: slightly OTM is optimal (leverage + lower cost) ────────────
    pct  = (strike - current_price) / current_price * 100
    otm  = pct if opt_type == "call" else -pct   # positive = OTM
    if   0   <= otm <= 3:  score += 30            # ATM / just OTM — sweet spot
    elif 3   <  otm <= 7:  score += 22
    elif -3  <= otm <  0:  score += 18            # slightly ITM
    elif 7   <  otm <= 12: score += 10
    # else: deep ITM / far OTM → 0

    # ── Open Interest: proxy for liquidity ────────────────────────────────────
    if   oi >= 2000: score += 25
    elif oi >= 500:  score += 20
    elif oi >= 100:  score += 12
    elif oi >= 10:   score += 5

    # ── Today's volume: shows active interest ─────────────────────────────────
    if   vol >= 1000: score += 20
    elif vol >= 200:  score += 15
    elif vol >= 30:   score += 8
    elif vol >= 5:    score += 3

    # ── Bid/ask spread: tighter = more liquid ────────────────────────────────
    if bid > 0 and ask > 0:
        mid        = (bid + ask) / 2
        spread_pct = (ask - bid) / mid * 100 if mid else 100
        if   spread_pct < 5:   score += 15
        elif spread_pct < 15:  score += 8
        elif spread_pct < 30:  score += 3

    # ── Implied Volatility: sweet spot 20-60% (not too cheap, not too pricey) ─
    if   0.20 <= iv <= 0.50: score += 10
    elif 0.50 <  iv <= 0.80: score += 6
    elif 0.10 <= iv <  0.20: score += 4

    return min(score, 100.0)


def get_recommendations(
    symbol: str,
    price: float,
    prediction: str,
    confidence: float,
    rsi: Optional[float] = None,
    macd: Optional[float] = None,
    change_pct: Optional[float] = None,
    top_n: int = 2,
) -> list[dict]:
    """
    Return up to top_n call or put recommendations for a given stock signal.
    Returns [] if NEUTRAL, low confidence, or no options data available.
    """
    if not is_optionable(symbol, price):
        return []
    if confidence < 0.55 or prediction not in ("BULLISH", "BEARISH"):
        return []

    chain = fetch_option_chain(symbol)
    if chain is None:
        return []

    opt_type = "call" if prediction == "BULLISH" else "put"
    df = chain["calls"] if opt_type == "call" else chain["puts"]
    if df.empty:
        return []

    recs = []
    for _, row in df.iterrows():
        row_d = row.to_dict()
        sc = _score_contract(row_d, price, opt_type)
        if sc < 25:
            continue

        def _sf(v, d=0.0):
            try:
                f = float(v); return d if f != f else f
            except (TypeError, ValueError):
                return d
        def _si(v, d=0):
            try:
                f = float(v); return d if f != f else int(f)
            except (TypeError, ValueError):
                return d

        bid    = _sf(row_d.get("bid"))
        ask    = _sf(row_d.get("ask"))
        last   = _sf(row_d.get("lastPrice"))
        iv     = _sf(row_d.get("impliedVolatility"))
        oi     = _si(row_d.get("openInterest"))
        vol    = _si(row_d.get("volume"))
        expiry = str(row_d.get("expiry") or "")

        # Days until expiry
        try:
            days_out = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
        except Exception:
            days_out = 0

        # Human-readable reasoning
        bullets: list[str] = [f"{confidence*100:.0f}% {prediction.lower()}"]
        if prediction == "BULLISH":
            if rsi and rsi < 45:       bullets.append("RSI oversold — room to run")
            elif rsi and rsi < 55:     bullets.append("RSI neutral — upside room")
            if macd and macd > 0:      bullets.append("MACD positive crossover")
            if change_pct and change_pct > 1.5: bullets.append(f"+{change_pct:.1f}% today")
        else:
            if rsi and rsi > 70:       bullets.append("RSI overbought")
            elif rsi and rsi > 60:     bullets.append("RSI elevated — reversal risk")
            if macd and macd < 0:      bullets.append("MACD turning negative")
            if change_pct and change_pct < -1.5: bullets.append(f"{change_pct:.1f}% today")

        recs.append({
            "symbol":        symbol,
            "type":          opt_type.upper(),
            "strike":        float(row_d.get("strike") or 0),
            "expiry":        expiry,
            "days_out":      days_out,
            "bid":           bid,
            "ask":           ask,
            "last":          last,
            "iv":            iv,
            "open_interest": oi,
            "volume":        vol,
            "score":         sc,
            "confidence":    confidence,
            "reason":        " · ".join(bullets),
            "current_price": price,
        })

    recs.sort(key=lambda x: x["score"], reverse=True)
    return recs[:top_n]
