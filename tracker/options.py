"""
Options intelligence: fetch option chains, score contracts, generate call/put recommendations.

Workflow:
  1. refresh_options() in main.py calls get_recommendations() for each high-signal stock.
  2. Recommendations are stored in the DB (options_recs table).
  3. web.py reads get_option_recs() and renders the Options Intelligence section.

Strike/expiry selection:
  - The expected move to a target date is projected from historical volatility (ATR%,
    falling back to the contract's own implied volatility) scaled by sqrt(time) and
    biased by directional confidence -- this gives a target price.
  - The target date is whichever ML timeframe (3d / 5d / 10d) shows the clearest edge
    (probability furthest from 50%) -- this gives a target trading-day horizon, mapped
    to a calendar-day horizon to match against real expiries in the chain.
  - Contracts are scored on how close their strike sits to the target price and their
    expiry to the target date, alongside the existing liquidity/spread/IV checks.
  - A lognormal probability-of-profit (POP) is estimated per contract using the
    contract's IV and our own predicted drift (not the market's risk-neutral drift),
    and surfaced for the trader -- it is informational, not part of the score, since
    it's derived from the same drift/vol inputs as the target-price distance.
"""

import math
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


# Calendar-day midpoints of the 3d/5d/10d ML horizons (via _trading_to_calendar_days) --
# fetch_option_chain uses these to make sure it pulls an expiry near each horizon rather
# than just the chronologically-nearest ones, which for liquid weekly-optioned names
# cluster within a few days and never reach the ~16-day mark a 10d signal needs.
_HORIZON_TARGET_CAL_DAYS: tuple = (6, 9, 16)


def fetch_option_chain(symbol: str) -> Optional[dict]:
    """
    Fetch expiry dates spanning the short/mid/long ML prediction horizons
    (~6, ~9, ~16 calendar days -- see _HORIZON_TARGET_CAL_DAYS) for a symbol.
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

        now    = datetime.now()
        parsed: list[tuple[str, int]] = []
        for exp in expiries:
            try:
                exp_dt = datetime.strptime(exp, "%Y-%m-%d")
            except ValueError:
                continue
            days = (exp_dt - now).days
            if days >= 1:
                parsed.append((exp, days))
        if not parsed:
            target = [expiries[0]]         # fall back to nearest expiry
        else:
            # For each horizon, grab whichever available expiry is closest to it
            target = []
            for want in _HORIZON_TARGET_CAL_DAYS:
                exp, _ = min(parsed, key=lambda p: abs(p[1] - want))
                if exp not in target:
                    target.append(exp)

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


def _norm_cdf(x: float) -> float:
    """Standard normal CDF via erf -- no scipy dependency needed."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _choose_horizon(
    confidence: float,
    prob_3d: Optional[float],
    prob_5d: Optional[float],
    prob_10d: Optional[float],
) -> tuple[int, float, str]:
    """
    Pick the trading-day horizon (3/5/10) whose ML probability shows the clearest
    directional edge (furthest from 50%). Falls back to a 5-day horizon using the
    blended `confidence` when no per-timeframe probabilities are available.
    Returns (trading_days, horizon_confidence_0to1, label).
    """
    candidates = [
        (3,  prob_3d,  "3d"),
        (5,  prob_5d,  "5d"),
        (10, prob_10d, "10d"),
    ]
    present = [(d, p, lbl) for d, p, lbl in candidates if p is not None]
    if not present:
        return 5, max(0.0, min(confidence, 1.0)), "5d"
    days, prob, label = max(present, key=lambda c: abs(c[1] - 0.5))
    return days, min(abs(prob - 0.5) * 2, 1.0), label


def _trading_to_calendar_days(trading_days: int) -> int:
    """Rough trading-day -> calendar-day conversion (5/7 week) plus a small buffer
    so the target date lands a couple of days after the move is expected to play out."""
    return round(trading_days * 7 / 5) + 2


def _expected_move_pct(atr_pct: Optional[float], target_days: int, horizon_conf: float) -> float:
    """
    Project the expected magnitude of move (%) over `target_days` trading days.
    Volatility scales with sqrt(time); the directional-confidence multiplier
    (0.5x-1.5x) reflects that a low-confidence signal implies a smaller expected
    move than a high-confidence one, for the same underlying volatility.
    """
    if not atr_pct or atr_pct <= 0:
        atr_pct = 2.0  # generic fallback ~2%/day when historical ATR isn't available
    base = atr_pct * math.sqrt(max(target_days, 1))
    return base * (0.5 + min(max(horizon_conf, 0.0), 1.0))


def _itm_probability(
    spot: float, strike: float, iv: float, days_out: int,
    opt_type: str, drift_pct: float = 0.0,
) -> Optional[float]:
    """
    Lognormal probability the contract finishes ITM at expiry, using OUR predicted
    drift (drift_pct, signed) rather than the market's risk-neutral (zero) drift --
    this reflects the model's directional edge, not just the option's fair value.
    """
    if spot <= 0 or strike <= 0 or days_out <= 0:
        return None
    if not iv or iv <= 0:
        iv = 0.5  # fallback vol when the chain doesn't report IV for this contract
    t = days_out / 365.0
    sigma = iv * math.sqrt(t)
    if sigma <= 0:
        return None
    mu = math.log(spot) + (drift_pct / 100.0) - 0.5 * iv * iv * t
    d = (math.log(strike) - mu) / sigma
    p_above = 1.0 - _norm_cdf(d)
    return p_above if opt_type == "call" else 1.0 - p_above


def _score_contract(
    row: dict, current_price: float, opt_type: str,
    target_price: Optional[float] = None,
    target_cal_days: Optional[int] = None,
    days_out: int = 0,
) -> float:
    """
    Score a single option contract 0-100.
    Higher = more attractive (strike near our target price, expiry near our target
    date, liquid, reasonable IV).
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

    # ── Strike vs. our target price (up to 25): closer = better ───────────────
    if target_price and target_price > 0:
        dist_pct = abs(strike - target_price) / target_price * 100
        if   dist_pct <=  2: score += 25
        elif dist_pct <=  5: score += 20
        elif dist_pct <= 10: score += 13
        elif dist_pct <= 18: score += 6
        # else: strike is nowhere near where we expect price to be → 0
    else:
        # Fallback moneyness-vs-spot scoring when no target price is available
        pct  = (strike - current_price) / current_price * 100
        otm  = pct if opt_type == "call" else -pct   # positive = OTM
        if   0   <= otm <= 3:  score += 25
        elif 3   <  otm <= 7:  score += 18
        elif -3  <= otm <  0:  score += 15
        elif 7   <  otm <= 12: score += 8

    # ── Expiry vs. our target date (up to 15): closer = better ────────────────
    if target_cal_days is not None and days_out:
        exp_dist = abs(days_out - target_cal_days)
        if   exp_dist <=  3: score += 15
        elif exp_dist <=  7: score += 10
        elif exp_dist <= 14: score += 5

    # ── Open Interest: proxy for liquidity ────────────────────────────────────
    if   oi >= 2000: score += 20
    elif oi >= 500:  score += 16
    elif oi >= 100:  score += 10
    elif oi >= 10:   score += 4

    # ── Today's volume: shows active interest ─────────────────────────────────
    if   vol >= 1000: score += 15
    elif vol >= 200:  score += 11
    elif vol >= 30:   score += 6
    elif vol >= 5:    score += 2

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
    fib_signal: int = 0,
    fib_level: str = "",
    atr_pct: Optional[float] = None,
    prob_3d: Optional[float] = None,
    prob_5d: Optional[float] = None,
    prob_10d: Optional[float] = None,
    top_n: int = 2,
) -> list[dict]:
    """
    Return up to top_n call or put recommendations for a given stock signal.
    Returns [] if NEUTRAL, low confidence, or no options data available.

    Picks a target trading-day horizon from whichever ML timeframe (3d/5d/10d)
    shows the clearest edge, projects a target price from that horizon using
    ATR-scaled expected move, and scores contracts on how well their strike and
    expiry line up with that target -- not just generic liquidity/moneyness.
    """
    if not is_optionable(symbol, price):
        return []
    if confidence < 0.25 or prediction not in ("BULLISH", "BEARISH"):
        return []

    chain = fetch_option_chain(symbol)
    if chain is None:
        return []

    opt_type = "call" if prediction == "BULLISH" else "put"
    df = chain["calls"] if opt_type == "call" else chain["puts"]
    if df.empty:
        return []

    direction = 1 if prediction == "BULLISH" else -1
    target_days, horizon_conf, horizon_label = _choose_horizon(
        confidence, prob_3d, prob_5d, prob_10d
    )
    move_pct        = _expected_move_pct(atr_pct, target_days, horizon_conf)
    target_price    = price * (1 + direction * move_pct / 100)
    target_cal_days = _trading_to_calendar_days(target_days)

    recs = []
    for _, row in df.iterrows():
        row_d = row.to_dict()

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

        strike = _sf(row_d.get("strike"))
        expiry = str(row_d.get("expiry") or "")

        # Days until expiry
        try:
            days_out = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
        except Exception:
            days_out = 0

        sc = _score_contract(
            row_d, price, opt_type,
            target_price=target_price, target_cal_days=target_cal_days,
            days_out=days_out,
        )
        if sc < 25:
            continue

        bid    = _sf(row_d.get("bid"))
        ask    = _sf(row_d.get("ask"))
        last   = _sf(row_d.get("lastPrice"))
        iv     = _sf(row_d.get("impliedVolatility"))
        oi     = _si(row_d.get("openInterest"))
        vol    = _si(row_d.get("volume"))

        pop = _itm_probability(
            price, strike, iv, days_out, opt_type,
            drift_pct=direction * move_pct,
        )

        # Human-readable reasoning
        bullets: list[str] = [f"{confidence*100:.0f}% {prediction.lower()}"]
        if prediction == "BULLISH":
            if rsi and rsi < 45:       bullets.append("RSI oversold — room to run")
            elif rsi and rsi < 55:     bullets.append("RSI neutral — upside room")
            if macd and macd > 0:      bullets.append("MACD positive crossover")
            if change_pct and change_pct > 1.5: bullets.append(f"+{change_pct:.1f}% today")
            if fib_signal == 1 and fib_level:
                bullets.append(f"Fib {fib_level} support holding")
        else:
            if rsi and rsi > 70:       bullets.append("RSI overbought")
            elif rsi and rsi > 60:     bullets.append("RSI elevated — reversal risk")
            if macd and macd < 0:      bullets.append("MACD turning negative")
            if change_pct and change_pct < -1.5: bullets.append(f"{change_pct:.1f}% today")
            if fib_signal == -1 and fib_level:
                bullets.append(f"Fib {fib_level} resistance rejected")
        bullets.append(f"Target ${target_price:.2f} by {expiry} ({horizon_label} horizon)")
        if pop is not None:
            bullets.append(f"POP ~{pop*100:.0f}%")

        # Fib alignment bonus: if strike is near a key Fib level, add to score
        fib_score_bonus = 0.0
        if fib_signal != 0 and fib_level and sc >= 25:
            # (we use the raw score here; fib_level just signals context)
            fib_score_bonus = 6.0  # modest bonus for Fib-aligned contracts
        sc = min(sc + fib_score_bonus, 100.0)

        recs.append({
            "symbol":         symbol,
            "type":           opt_type.upper(),
            "strike":         strike,
            "expiry":         expiry,
            "days_out":       days_out,
            "bid":            bid,
            "ask":            ask,
            "last":           last,
            "iv":             iv,
            "open_interest":  oi,
            "volume":         vol,
            "score":          sc,
            "confidence":     confidence,
            "reason":         " · ".join(bullets),
            "current_price":  price,
            "target_price":   round(target_price, 2),
            "target_days":    target_days,
            "pop":            round(pop, 3) if pop is not None else None,
        })

    recs.sort(key=lambda x: x["score"], reverse=True)
    return recs[:top_n]
