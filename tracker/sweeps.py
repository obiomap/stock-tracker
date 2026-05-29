"""
sweeps.py -- Options sweeps, golden sweeps, and dark pool block detection.

Data sources (yfinance only — no paid APIs required):
  Options sweeps : scan chains for vol/OI >= 2.5x + total premium >= $10k
  Golden sweeps  : options sweeps with total premium >= $100k (institutional)
  Dark pool      : high vol + muted price action = off-exchange block activity
"""

import time
from datetime import datetime

from .options import fetch_option_chain, is_optionable
from . import database as db

# ── Detection thresholds ──────────────────────────────────────────────────────

SWEEP_MIN_CONTRACTS  = 50        # minimum contract volume per strike
SWEEP_MIN_VOL_OI     = 2.5       # vol >= 2.5x open interest (fresh positioning)
SWEEP_MIN_PREMIUM    = 10_000    # $10k total premium floor
GOLDEN_MIN_PREMIUM   = 100_000   # $100k = golden (institutional) sweep

DP_VOL_RATIO_MIN     = 2.5       # volume >= 2.5x 20-day avg
DP_PRICE_CHG_MAX     = 1.5       # absolute price change % (muted = institutional)
DP_MIN_VOLUME        = 200_000   # minimum share volume

# Liquid top-tier names always worth scanning even without unusual volume
_TOP_LIQUID = frozenset({
    "SPY","QQQ","AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD",
    "PLTR","BABA","TSM","SOFI","COIN","MSTR","HOOD","SHOP","NET","CRWD",
    "BIDU","JD","PDD","SE","GRAB","INFY","HDB","TM","SONY","NIO",
})


# ── helpers ───────────────────────────────────────────────────────────────────

def _sf(v, d=0.0):
    try:
        f = float(v)
        return d if f != f else f
    except Exception:
        return d


def _si(v, d=0):
    try:
        f = float(v)
        return d if f != f else int(f)
    except Exception:
        return d


# ── Options sweep scanner ─────────────────────────────────────────────────────

def _scan_options_sweeps(symbol: str, price: float) -> list[dict]:
    """Scan one symbol's options chain for sweep activity."""
    chain = fetch_option_chain(symbol)
    if not chain:
        return []

    now_str = datetime.now().isoformat()
    found   = []

    for opt_type, df in [("CALL", chain["calls"]), ("PUT", chain["puts"])]:
        if df.empty:
            continue
        for _, row in df.iterrows():
            r      = row.to_dict()
            vol    = _si(r.get("volume"))
            oi     = _si(r.get("openInterest"))
            last   = _sf(r.get("lastPrice"))
            bid    = _sf(r.get("bid"))
            ask    = _sf(r.get("ask"))
            strike = _sf(r.get("strike"))
            iv     = _sf(r.get("impliedVolatility"))
            expiry = str(r.get("expiry") or "")

            if vol < SWEEP_MIN_CONTRACTS:
                continue
            vol_oi = vol / max(oi, 1)
            if vol_oi < SWEEP_MIN_VOL_OI:
                continue
            mid = last if last > 0 else ((bid + ask) / 2 if (bid + ask) > 0 else 0)
            if mid <= 0:
                continue
            premium = mid * vol * 100
            if premium < SWEEP_MIN_PREMIUM:
                continue

            try:
                days_out = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
            except Exception:
                days_out = 0
            if days_out < 0:
                continue

            otm_pct    = (strike - price) / price * 100 if price > 0 else 0
            if opt_type == "PUT":
                otm_pct = -otm_pct
            aggression = (
                min((mid - bid) / max(ask - bid, 0.001), 1.0) if ask > bid else 0.5
            )
            is_golden = premium >= GOLDEN_MIN_PREMIUM

            found.append({
                "sweep_type":    "GOLDEN_SWEEP" if is_golden else f"{opt_type}_SWEEP",
                "symbol":        symbol,
                "direction":     "BULLISH" if opt_type == "CALL" else "BEARISH",
                "opt_type":      opt_type,
                "strike":        strike,
                "expiry":        expiry,
                "days_out":      days_out,
                "opt_volume":    vol,
                "open_interest": oi,
                "vol_oi_ratio":  round(vol_oi, 1),
                "last_price":    round(mid, 2),
                "iv_pct":        round(iv * 100, 1),
                "total_premium": round(premium),
                "otm_pct":       round(otm_pct, 1),
                "aggression":    round(aggression, 2),
                "current_price": price,
                "notional":      0.0,
                "vol_ratio":     0.0,
                "change_pct":    0.0,
                "is_golden":     is_golden,
                "created_at":    now_str,
            })

    found.sort(key=lambda x: x["total_premium"], reverse=True)
    return found[:5]


# ── Dark pool block scanner ───────────────────────────────────────────────────

def _scan_dark_pool(all_stocks: list[dict]) -> list[dict]:
    """
    Detect dark pool block activity from existing stock snapshots.
    High volume + muted price impact = institutional off-exchange accumulation/distribution.
    """
    blocks  = []
    now_str = datetime.now().isoformat()

    for s in all_stocks:
        sym     = s.get("symbol", "")
        price   = s.get("price") or 0
        vol     = s.get("volume") or 0
        avg_vol = s.get("avg_volume") or 0
        chg     = s.get("change_pct") or 0

        if "-USD" in sym or ".L" in sym:
            continue
        if price < 5 or avg_vol < 100_000 or vol < DP_MIN_VOLUME:
            continue
        vol_ratio = vol / avg_vol
        if vol_ratio < DP_VOL_RATIO_MIN:
            continue
        if abs(chg) > DP_PRICE_CHG_MAX:
            continue

        notional  = price * vol
        dp_score  = min(vol_ratio * (1.5 - abs(chg) / 10) * 8, 100)
        direction = "ACCUMULATION" if chg >= 0 else "DISTRIBUTION"

        blocks.append({
            "sweep_type":    "DARK_POOL",
            "symbol":        sym,
            "direction":     direction,
            "opt_type":      "",
            "strike":        0.0,
            "expiry":        "",
            "days_out":      0,
            "opt_volume":    0,
            "open_interest": 0,
            "vol_oi_ratio":  0.0,
            "last_price":    0.0,
            "iv_pct":        0.0,
            "total_premium": 0.0,
            "otm_pct":       0.0,
            "aggression":    0.0,
            "current_price": price,
            "notional":      round(notional),
            "vol_ratio":     round(vol_ratio, 1),
            "change_pct":    round(chg, 2),
            "is_golden":     False,
            "created_at":    now_str,
        })

    blocks.sort(key=lambda x: x["notional"], reverse=True)
    return blocks[:10]


# ── Main entry point ──────────────────────────────────────────────────────────

def refresh_sweeps(watchlist: list[str], stocks_db: dict) -> dict:
    """
    Full sweep scan. Called from the main polling loop.
    Returns counts of what was found.
    """
    # Build candidate list: top liquid + unusual volume + strong AI signal
    candidates: list[str] = []
    for sym in watchlist:
        s = stocks_db.get(sym)
        if not s:
            continue
        p = s.get("price") or 0
        if not is_optionable(sym, p):
            continue
        vol_ratio  = (s.get("volume") or 0) / max(s.get("avg_volume") or 1, 1)
        has_signal = (
            s.get("prediction") in ("BULLISH", "BEARISH")
            and (s.get("prediction_confidence") or 0) >= 0.40
        )
        if sym in _TOP_LIQUID or vol_ratio >= 1.5 or has_signal:
            candidates.append(sym)

    candidates = candidates[:50]
    print(f"[sweeps] scanning {len(candidates)} candidates for options sweeps")

    all_opt_sweeps: list[dict] = []
    for sym in candidates:
        p = (stocks_db.get(sym) or {}).get("price") or 0
        if p <= 0:
            continue
        try:
            found = _scan_options_sweeps(sym, p)
            if found:
                print(f"[sweeps] {sym}: {len(found)} sweep(s), top premium ${found[0]['total_premium']:,.0f}")
            all_opt_sweeps.extend(found)
        except Exception as e:
            print(f"[sweeps] {sym} error: {e}")
        time.sleep(0.25)

    dark_blocks = _scan_dark_pool(list(stocks_db.values()))
    print(f"[sweeps] dark pool blocks: {len(dark_blocks)}")

    db.upsert_sweeps(all_opt_sweeps + dark_blocks)

    golden = [s for s in all_opt_sweeps if s["is_golden"]]
    opts   = [s for s in all_opt_sweeps if not s["is_golden"]]
    return {"golden": len(golden), "opts": len(opts), "dark_pool": len(dark_blocks)}
