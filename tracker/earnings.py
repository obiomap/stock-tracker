from datetime import datetime, timezone, timedelta
from typing import Optional
import pandas as pd
from . import data as fetcher
from . import database as db


def _days_until(dt) -> Optional[int]:
    try:
        if hasattr(dt, "tzinfo") and dt.tzinfo is not None:
            now = datetime.now(timezone.utc)
            return (dt.replace(tzinfo=timezone.utc) - now).days
        else:
            now = datetime.now()
            target = pd.Timestamp(dt).to_pydatetime()
            return (target - now).days
    except Exception:
        return None


def _avg_historical_reaction(symbol: str, hist_df: pd.DataFrame) -> Optional[float]:
    """Compute average next-day % change following past earnings announcements."""
    try:
        earn_df = fetcher.fetch_earnings_history(symbol)
        if earn_df is None or earn_df.empty:
            return None

        # Normalize index to date only (no tz)
        earn_dates = []
        for idx in earn_df.index:
            try:
                d = pd.Timestamp(idx).tz_convert(None).normalize()
                earn_dates.append(d)
            except Exception:
                try:
                    earn_dates.append(pd.Timestamp(idx).normalize())
                except Exception:
                    pass

        reactions = []
        price_index = hist_df.index.tz_localize(None) if hist_df.index.tz else hist_df.index
        price_index = price_index.normalize()

        for ed in earn_dates[:8]:  # look at last 8 quarters
            try:
                pos = price_index.get_loc(ed)
                if isinstance(pos, slice):
                    pos = pos.start
                if pos + 1 < len(hist_df):
                    day_after = hist_df["Close"].iloc[pos + 1]
                    day_of = hist_df["Close"].iloc[pos]
                    reactions.append((day_after - day_of) / day_of * 100)
            except Exception:
                continue

        if reactions:
            return round(sum(reactions) / len(reactions), 2)
        return None
    except Exception:
        return None


def refresh_earnings_calendar(symbols: list[str], hist_data: dict) -> list[dict]:
    results = []
    now = datetime.now(timezone.utc)

    for symbol in symbols:
        cal = fetcher.fetch_calendar(symbol)
        if not cal:
            continue

        earnings_dates = cal.get("Earnings Date") or []
        if not earnings_dates:
            continue

        next_date = earnings_dates[0] if earnings_dates else None
        if next_date is None:
            continue

        days = _days_until(next_date)
        if days is None or days < -1:
            continue

        eps_est = cal.get("Earnings Average")
        hist = hist_data.get(symbol, {}).get("hist")
        avg_reaction = _avg_historical_reaction(symbol, hist) if hist is not None else None

        entry = {
            "symbol": symbol,
            "earnings_date": str(pd.Timestamp(next_date).date()),
            "eps_estimate": round(float(eps_est), 2) if eps_est else None,
            "actual_eps": None,
            "surprise_pct": None,
            "avg_reaction_pct": avg_reaction,
            "days_until": days,
            "is_upcoming": 1 if days >= 0 else 0,
        }
        db.upsert_earnings(entry)
        results.append(entry)

    return sorted(results, key=lambda x: x["days_until"])
