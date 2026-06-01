"""
Catalyst/news signal detection for focus-group stocks.
Fetches yfinance headlines, classifies by catalyst type, and returns
signals ready for alert injection. Results are cached for 1 hour per symbol
so the 5-minute refresh loop doesn't hammer the API.
"""
import time
from datetime import datetime, timedelta
from typing import Optional

CATALYST_KEYWORDS: dict[str, list[str]] = {
    "EARNINGS":   ["earnings", "beat", "miss", "eps", "revenue", "guidance",
                   "forecast", "quarterly results", "q1", "q2", "q3", "q4"],
    "UPGRADE":    ["upgrade", "outperform", "overweight", "buy rating",
                   "price target raised", "pt raised", "bullish"],
    "DOWNGRADE":  ["downgrade", "underperform", "underweight", "sell rating",
                   "price target cut", "pt cut", "bearish"],
    "LAUNCH":     ["launch", "unveil", "announce", "debut", "release", "ship",
                   "available", "introduce", "reveal"],
    "DEAL":       ["deal", "partnership", "contract", "agreement", "acquisition",
                   "merger", "joint venture", "invest", "fund"],
    "REGULATORY": ["fda", "sec", "cftc", "regulation", "approval", "approved",
                   "rejected", "fine", "lawsuit", "ban", "export control"],
    "MACRO":      ["fed", "rate hike", "rate cut", "inflation", "gdp",
                   "tariff", "trade war", "interest rate"],
}

_CACHE_TTL = 3600   # seconds; re-fetch after 1 hour
_cache: dict[str, tuple[float, list]] = {}   # symbol -> (timestamp, raw_items)


def fetch_news_signals(symbols: list[str],
                       max_age_hours: int = 24) -> dict[str, list[dict]]:
    """
    Returns {symbol: [catalyst_dict, ...]} for symbols with actionable recent news.
    catalyst_dict keys: headline (str), type (str), published (datetime|None), url (str).
    Only the first matching catalyst type per article is returned.
    """
    try:
        import yfinance as yf
    except ImportError:
        return {}

    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    results: dict[str, list[dict]] = {}

    for sym in symbols:
        now_ts = time.time()
        cached_ts, cached_items = _cache.get(sym, (0.0, []))

        if now_ts - cached_ts < _CACHE_TTL:
            raw = cached_items
        else:
            try:
                raw = yf.Ticker(sym).news or []
                _cache[sym] = (now_ts, raw)
                time.sleep(0.15)   # gentle on the API
            except Exception:
                raw = []

        catalysts = []
        for item in raw[:10]:
            pub_ts = item.get("providerPublishTime")
            pub_dt = datetime.utcfromtimestamp(pub_ts) if pub_ts else None
            if pub_dt and pub_dt < cutoff:
                continue
            cat_type = _classify(item.get("title") or "")
            if cat_type:
                catalysts.append({
                    "headline":  item.get("title", ""),
                    "type":      cat_type,
                    "published": pub_dt,
                    "url":       item.get("link", ""),
                })

        if catalysts:
            results[sym] = catalysts

    return results


def _classify(title: str) -> Optional[str]:
    lowered = title.lower()
    for cat_type, keywords in CATALYST_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return cat_type
    return None


def build_news_html_section(news_signals: dict[str, list[dict]]) -> str:
    """
    Returns an HTML <div> block listing catalyst headlines for injection into
    alert emails. Returns empty string if no signals.
    """
    if not news_signals:
        return ""

    TYPE_COLORS = {
        "EARNINGS":   ("#fbbf24", "#451a03"),
        "UPGRADE":    ("#22c55e", "#14532d"),
        "DOWNGRADE":  ("#ef4444", "#7f1d1d"),
        "LAUNCH":     ("#818cf8", "#1e1b4b"),
        "DEAL":       ("#38bdf8", "#0c4a6e"),
        "REGULATORY": ("#f97316", "#431407"),
        "MACRO":      ("#94a3b8", "#1e293b"),
    }

    rows = ""
    for sym, catalysts in sorted(news_signals.items()):
        for cat in catalysts[:2]:   # cap at 2 headlines per symbol
            col, bg = TYPE_COLORS.get(cat["type"], ("#94a3b8", "#1e293b"))
            pub_str = (cat["published"].strftime("%H:%M UTC")
                       if cat["published"] else "")
            link = cat.get("url", "")
            headline_html = (
                f'<a href="{link}" style="color:#e2e8f0;text-decoration:none">'
                f'{cat["headline"]}</a>'
                if link else cat["headline"]
            )
            rows += (
                f'<tr style="border-bottom:1px solid #1e293b">'
                f'<td style="padding:8px 12px;font-weight:700;color:#f1f5f9">{sym}</td>'
                f'<td style="padding:8px 12px;text-align:center">'
                f'<span style="background:{bg};color:{col};padding:2px 8px;'
                f'border-radius:4px;font-size:11px;font-weight:700">{cat["type"]}</span></td>'
                f'<td style="padding:8px 12px;color:#e2e8f0;font-size:13px">{headline_html}</td>'
                f'<td style="padding:8px 12px;color:#64748b;font-size:12px;white-space:nowrap">'
                f'{pub_str}</td>'
                f'</tr>'
            )

    if not rows:
        return ""

    return f"""
  <div style="margin-bottom:28px">
    <h3 style="margin:0 0 10px;color:#f1f5f9;font-size:15px;font-weight:700;
               display:flex;align-items:center;gap:8px">
      <span style="background:rgba(56,189,248,.15);border:1px solid rgba(56,189,248,.4);
                   padding:3px 10px;border-radius:6px;font-size:13px">&#x1F4F0;</span>
      Focus Group Catalysts
    </h3>
    <table border="0" cellspacing="0" cellpadding="0"
           style="border-collapse:collapse;width:100%;border-radius:10px;
                  overflow:hidden;background:#1e293b;border:1px solid #334155">
      <tr style="background:#0f172a">
        <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:11px;
                   font-weight:600;text-transform:uppercase;letter-spacing:.06em">Symbol</th>
        <th style="padding:8px 12px;text-align:center;color:#64748b;font-size:11px;
                   font-weight:600;text-transform:uppercase;letter-spacing:.06em">Type</th>
        <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:11px;
                   font-weight:600;text-transform:uppercase;letter-spacing:.06em">Headline</th>
        <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:11px;
                   font-weight:600;text-transform:uppercase;letter-spacing:.06em">Published</th>
      </tr>
      {rows}
    </table>
  </div>"""
