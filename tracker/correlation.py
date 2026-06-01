"""
Focus-group correlation and divergence detection.
Flags when one stock in the group moves significantly against the group average
using a z-score approach on same-day percentage changes.
"""
import numpy as np

DEFAULT_FOCUS_GROUP = ["ARM", "AMD", "NVDA", "NVTS", "TSLA", "CRWV", "FCEL"]


def compute_divergence(stocks: list[dict], focus_symbols: list[str]) -> list[dict]:
    """
    Returns divergence alerts for focus stocks whose % change is ≥2σ from the
    group mean. Requires at least 3 stocks with valid change_pct to fire.
    """
    focus = [
        s for s in stocks
        if s["symbol"] in focus_symbols and s.get("change_pct") is not None
    ]
    if len(focus) < 3:
        return []

    changes = [s["change_pct"] for s in focus]
    avg = float(np.mean(changes))
    std = float(np.std(changes))
    if std < 0.5:   # group is moving tightly together — no divergence signal
        return []

    alerts = []
    for s in focus:
        chg = s["change_pct"]
        z = (chg - avg) / std
        if abs(z) >= 2.0:
            direction = "outperforming" if chg > avg else "lagging"
            alerts.append({
                "symbol":    s["symbol"],
                "change_pct": chg,
                "group_avg": avg,
                "z_score":   z,
                "direction": direction,
                "message": (
                    f"{s['symbol']} {direction} AI focus group: "
                    f"{chg:+.1f}% vs group avg {avg:+.1f}% (z={z:.1f}σ)"
                ),
                "severity": "HIGH" if abs(z) >= 2.5 else "MEDIUM",
            })
    return alerts


def group_summary(stocks: list[dict], focus_symbols: list[str]) -> dict:
    """Returns summary stats for the focus group keyed by symbol list order."""
    focus = [
        s for s in stocks
        if s["symbol"] in focus_symbols and s.get("change_pct") is not None
    ]
    if not focus:
        return {}
    changes = [s["change_pct"] for s in focus]
    ordered = sorted(focus, key=lambda s: s["change_pct"], reverse=True)
    return {
        "avg_change": float(np.mean(changes)),
        "std_change": float(np.std(changes)),
        "top_gainer": ordered[0],
        "top_loser":  ordered[-1],
        "stocks":     ordered,
    }


def build_focus_html_section(stocks: list[dict], focus_symbols: list[str],
                              group_name: str = "AI Infrastructure Focus") -> str:
    """
    Returns an HTML <div> block summarising the focus group for injection into
    alert emails. Returns empty string if no focus stocks have data.
    """
    summary = group_summary(stocks, focus_symbols)
    if not summary:
        return ""

    def _chg_color(v):
        if v is None:
            return "#94a3b8"
        return "#22c55e" if v >= 0 else "#ef4444"

    def _fmt_price(v):
        if v is None:
            return "—"
        return f"${float(v):,.2f}"

    rows = ""
    for s in summary["stocks"]:
        chg  = s.get("change_pct") or 0
        rsi  = s.get("rsi")
        pred = s.get("prediction", "NEUTRAL")
        conf = s.get("prediction_confidence") or 0
        pred_col  = {"BULLISH": "#22c55e", "BEARISH": "#ef4444"}.get(pred, "#94a3b8")
        pred_bg   = {"BULLISH": "#14532d", "BEARISH": "#7f1d1d"}.get(pred, "#1e293b")
        arrow = "▲" if chg >= 0 else "▼"
        rows += (
            f'<tr style="border-bottom:1px solid #1e293b">'
            f'<td style="padding:8px 12px;font-weight:700;color:#f1f5f9">{s["symbol"]}</td>'
            f'<td style="padding:8px 12px;text-align:right;color:#e2e8f0">{_fmt_price(s.get("price"))}</td>'
            f'<td style="padding:8px 12px;text-align:center;color:{_chg_color(chg)};font-weight:700">'
            f'{arrow} {abs(chg):.2f}%</td>'
            f'<td style="padding:8px 12px;text-align:center;color:#cbd5e1">'
            f'{"&mdash;" if rsi is None else f"{float(rsi):.0f}"}</td>'
            f'<td style="padding:8px 12px;text-align:center">'
            f'<span style="background:{pred_bg};color:{pred_col};padding:2px 8px;'
            f'border-radius:4px;font-size:11px;font-weight:700">{pred} {conf*100:.0f}%</span>'
            f'</td>'
            f'</tr>'
        )

    avg     = summary["avg_change"]
    avg_col = "#22c55e" if avg >= 0 else "#ef4444"
    avg_arr = "▲" if avg >= 0 else "▼"

    return f"""
  <div style="margin-bottom:28px">
    <h3 style="margin:0 0 10px;color:#f1f5f9;font-size:15px;font-weight:700;
               display:flex;align-items:center;gap:8px">
      <span style="background:rgba(251,191,36,.15);border:1px solid rgba(251,191,36,.4);
                   padding:3px 10px;border-radius:6px;font-size:13px">&#x2B50;</span>
      {group_name} &mdash; Group Avg:
      <span style="color:{avg_col}">{avg_arr} {abs(avg):.2f}%</span>
    </h3>
    <table border="0" cellspacing="0" cellpadding="0"
           style="border-collapse:collapse;width:100%;border-radius:10px;
                  overflow:hidden;background:#1e293b;border:1px solid #334155">
      <tr style="background:#0f172a">
        <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:11px;
                   font-weight:600;text-transform:uppercase;letter-spacing:.06em">Symbol</th>
        <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:11px;
                   font-weight:600;text-transform:uppercase;letter-spacing:.06em">Price</th>
        <th style="padding:8px 12px;text-align:center;color:#64748b;font-size:11px;
                   font-weight:600;text-transform:uppercase;letter-spacing:.06em">Change</th>
        <th style="padding:8px 12px;text-align:center;color:#64748b;font-size:11px;
                   font-weight:600;text-transform:uppercase;letter-spacing:.06em">RSI</th>
        <th style="padding:8px 12px;text-align:center;color:#64748b;font-size:11px;
                   font-weight:600;text-transform:uppercase;letter-spacing:.06em">Signal</th>
      </tr>
      {rows}
    </table>
  </div>"""
