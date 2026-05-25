import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from . import database as db
from . import sms as sms_mod


# ── Resend (preferred) ────────────────────────────────────────────────────────

def _resend_api_key(config: dict) -> str:
    return os.environ.get("RESEND_API_KEY") or config.get("resend_api_key", "")


def _resend_from(config: dict) -> str:
    """Sender address — must be from a Resend-verified domain."""
    return (os.environ.get("RESEND_FROM")
            or config.get("resend_from", "")
            or config.get("email", {}).get("sender", "onboarding@resend.dev"))


def _can_send_resend(config: dict) -> bool:
    return bool(_resend_api_key(config))


def _send_via_resend(subject: str, html_body: str, to: str, config: dict) -> bool:
    try:
        import resend
        resend.api_key = _resend_api_key(config)
        resend.Emails.send({
            "from": _resend_from(config),
            "to": [to],
            "subject": subject,
            "html": html_body,
        })
        return True
    except Exception as e:
        print(f"[Resend error] {e}")
        return False


# ── SMTP fallback ─────────────────────────────────────────────────────────────

def _smtp_connection(config: dict):
    email_cfg = config.get("email", {})
    server = smtplib.SMTP(email_cfg["smtp_server"], email_cfg["smtp_port"])
    server.ehlo()
    server.starttls()
    server.login(email_cfg["sender"], email_cfg["password"])
    return server


def _can_send_smtp(config: dict) -> bool:
    email_cfg = config.get("email", {})
    return bool(email_cfg.get("enabled") and email_cfg.get("sender") and email_cfg.get("password"))


def _can_send(config: dict) -> bool:
    return _can_send_resend(config) or _can_send_smtp(config)


# ── Public interface ──────────────────────────────────────────────────────────

def send_email(subject: str, html_body: str, config: dict, recipient: str | None = None) -> bool:
    email_cfg = config.get("email", {})
    to = recipient or email_cfg.get("recipient", "")
    if not to:
        return False

    # Prefer Resend
    if _can_send_resend(config):
        return _send_via_resend(subject, html_body, to, config)

    # Fall back to SMTP
    if not _can_send_smtp(config):
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_cfg["sender"]
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))
    try:
        with _smtp_connection(config) as server:
            server.sendmail(email_cfg["sender"], to, msg.as_string())
        return True
    except Exception as e:
        print(f"[Email error] {e}")
        return False


def send_to_subscribers(subject: str, html_body: str, relevant_symbols: set[str], config: dict) -> int:
    """Email all active subscribers who track at least one relevant symbol."""
    if not _can_send(config):
        return 0
    subscribers = db.get_active_subscribers()
    sent = 0

    if _can_send_resend(config):
        # Resend: one call per subscriber
        for sub in subscribers:
            sub_stocks = set(sub["stocks"])
            if not sub_stocks or sub_stocks & relevant_symbols:
                if _send_via_resend(subject, html_body, sub["email"], config):
                    sent += 1
        return sent

    # SMTP fallback: reuse connection across subscribers
    try:
        conn = _smtp_connection(config)
    except Exception as e:
        print(f"[SMTP connect error] {e}")
        return 0
    try:
        for sub in subscribers:
            sub_stocks = set(sub["stocks"])
            if not sub_stocks or sub_stocks & relevant_symbols:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = config["email"]["sender"]
                msg["To"] = sub["email"]
                msg.attach(MIMEText(html_body, "html"))
                try:
                    conn.sendmail(config["email"]["sender"], sub["email"], msg.as_string())
                    sent += 1
                except Exception as e:
                    print(f"[Email error {sub['email']}] {e}")
    finally:
        try:
            conn.quit()
        except Exception:
            pass
    return sent


def _html_alert_row(bg: str, label: str, symbol: str, message: str) -> str:
    return f"""
    <tr style="background:{bg}">
        <td style="padding:8px;font-weight:bold">{label}</td>
        <td style="padding:8px;font-weight:bold">{symbol}</td>
        <td style="padding:8px">{message}</td>
    </tr>"""


def build_email_report(stocks: list[dict], earnings: list[dict], alerts: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def chg_color(v):
        if v is None: return "gray"
        return "#22c55e" if v >= 0 else "#ef4444"

    def sig_color(s):
        return {"BULLISH": "#22c55e", "BEARISH": "#ef4444"}.get(s, "#f59e0b")

    rows_stocks = ""
    for s in stocks:
        chg = s.get("change_pct", 0) or 0
        pred = s.get("prediction", "N/A")
        conf = s.get("prediction_confidence", 0) or 0
        display = s["symbol"].replace("-USD", "")
        rows_stocks += f"""
        <tr>
            <td style="padding:8px;font-weight:bold">{display}</td>
            <td style="padding:8px">${s.get('price','N/A')}</td>
            <td style="padding:8px;color:{chg_color(chg)}">{chg:+.2f}%</td>
            <td style="padding:8px">{s.get('rsi','N/A')}</td>
            <td style="padding:8px;color:{sig_color(pred)};font-weight:bold">{pred}</td>
            <td style="padding:8px">{conf*100:.0f}%</td>
        </tr>"""

    rows_earnings = ""
    for e in earnings[:10]:
        rxn = e.get("avg_reaction_pct")
        rxn_str = f"{rxn:+.1f}%" if rxn is not None else "N/A"
        rows_earnings += f"""
        <tr>
            <td style="padding:8px;font-weight:bold">{e['symbol']}</td>
            <td style="padding:8px">{e['earnings_date']}</td>
            <td style="padding:8px">{e['days_until']}d</td>
            <td style="padding:8px">{rxn_str}</td>
        </tr>"""

    rows_alerts = ""
    for a in alerts[:15]:
        bg = {"HIGH": "#fef2f2", "MEDIUM": "#fffbeb", "LOW": "#f0fdf4"}.get(a.get("severity", ""), "white")
        rows_alerts += _html_alert_row(bg, a.get("severity", ""), a.get("symbol", ""), a.get("message", ""))

    return f"""
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                       max-width:900px;margin:auto;background:#f8fafc;padding:24px">
    <div style="background:linear-gradient(135deg,#020617,#1e1b4b);color:white;
                border-radius:16px;padding:28px 32px;margin-bottom:24px">
      <h2 style="margin:0 0 4px">&#x1F4C8; Stock Tracker Report</h2>
      <p style="margin:0;opacity:.7;font-size:14px">{now}</p>
    </div>

    <h3 style="color:#1e293b">Watchlist</h3>
    <table border="0" cellspacing="0" cellpadding="0"
           style="border-collapse:collapse;width:100%;border-radius:12px;
                  overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.12)">
        <tr style="background:#1e3a8a;color:white">
            <th style="padding:10px 12px;text-align:left">Symbol</th>
            <th style="padding:10px 12px;text-align:right">Price</th>
            <th style="padding:10px 12px;text-align:right">Change</th>
            <th style="padding:10px 12px;text-align:center">RSI</th>
            <th style="padding:10px 12px;text-align:center">Signal</th>
            <th style="padding:10px 12px;text-align:right">Confidence</th>
        </tr>{rows_stocks}
    </table>

    <h3 style="color:#1e293b">Upcoming Earnings</h3>
    <table border="0" cellspacing="0" cellpadding="0"
           style="border-collapse:collapse;width:100%;border-radius:12px;
                  overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.12)">
        <tr style="background:#1e3a8a;color:white">
            <th style="padding:10px 12px;text-align:left">Symbol</th>
            <th style="padding:10px 12px;text-align:left">Date</th>
            <th style="padding:10px 12px;text-align:center">Days</th>
            <th style="padding:10px 12px;text-align:right">Avg Reaction</th>
        </tr>{rows_earnings}
    </table>

    <h3 style="color:#1e293b">Active Alerts</h3>
    <table border="0" cellspacing="0" cellpadding="0"
           style="border-collapse:collapse;width:100%;border-radius:12px;
                  overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.12)">
        <tr style="background:#1e3a8a;color:white">
            <th style="padding:10px 12px;text-align:left">Level</th>
            <th style="padding:10px 12px;text-align:left">Symbol</th>
            <th style="padding:10px 12px;text-align:left">Message</th>
        </tr>{rows_alerts}
    </table>

    <p style="color:#94a3b8;font-size:12px;margin-top:24px;text-align:center">
      Generated by Stock Tracker &bull; {now} &bull; Unsubscribe via your alert email link
    </p>
    </body></html>"""


def _payoff_svg(opt_type: str, strike: float, current_price: float,
                bid: float, ask: float) -> str:
    """
    Inline SVG payoff-at-expiry diagram for one option contract.
    Dark background; green/red fill zones; dashed lines for now/strike/BE.
    """
    mid = (bid + ask) / 2 if bid > 0 and ask > 0 else max(bid, ask, 0.01)

    W, H = 420, 110
    pl, pr, pt, pb = 46, 12, 14, 26   # padding: left, right, top, bottom
    pw = W - pl - pr
    ph = H - pt - pb

    # Breakeven price
    be = strike + mid if opt_type == "CALL" else strike - mid

    # X-axis range — wide enough to always show breakeven + current price
    x0 = min(strike * 0.84, be * 0.97, current_price * 0.93)
    x1 = max(strike * 1.16, be * 1.03, current_price * 1.07)
    pad_x = (x1 - x0) * 0.04
    x0 -= pad_x;  x1 += pad_x

    # Payoff function
    def pnl(price):
        return (max(price - strike, 0) - mid) if opt_type == "CALL" \
               else (max(strike - price, 0) - mid)

    # Y-axis range
    pnl_lo = -mid * 1.25
    pnl_hi = max(pnl(x1 if opt_type == "CALL" else x0), mid * 1.5) * 1.1

    def px(price): return pl + (price - x0) / (x1 - x0) * pw
    def py(p):     return pt + (pnl_hi - p) / (pnl_hi - pnl_lo) * ph

    zero_y   = py(0)
    strike_x = px(strike)
    curr_x   = max(pl, min(pl + pw, px(current_price)))
    be_x     = max(pl + 1, min(pl + pw - 1, px(be)))

    # Smooth polyline (80 segments)
    N = 80
    pts = [(px(x0 + (x1 - x0) * i / N), py(pnl(x0 + (x1 - x0) * i / N)))
           for i in range(N + 1)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    # Fill polygons
    # Loss region (always below zero line)
    if opt_type == "CALL":
        # flat −mid from left to strike, then diagonal up to be_x/zero_y
        loss_pts = [(pl, zero_y), (pl, py(-mid)),
                    (strike_x, py(-mid)), (be_x, zero_y)]
        # profit from be_x upward to right edge
        gain_pts = [(be_x, zero_y),
                    (pl + pw, py(pnl(x1))),
                    (pl + pw, zero_y)]
    else:
        # profit on left side, down to be_x
        gain_pts = [(pl, zero_y),
                    (pl, py(pnl(x0))),
                    (be_x, zero_y)]
        # flat −mid from be_x/zero_y to strike, then right edge
        loss_pts = [(be_x, zero_y),
                    (strike_x, py(-mid)),
                    (pl + pw, py(-mid)),
                    (pl + pw, zero_y)]

    def _pp(pts_list):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts_list)

    col = "#16a34a" if opt_type == "CALL" else "#dc2626"

    # Y-axis tick labels
    y_ticks = ""
    for val, lbl in [(-mid, f"-${mid:.2f}"), (0, "$0"),
                     (mid * 2, f"+${mid * 2:.2f}")]:
        yp = py(val)
        if pt - 2 <= yp <= H - pb + 2:
            y_ticks += (f'<text x="{pl - 3}" y="{yp + 3:.1f}" text-anchor="end" '
                        f'fill="#64748b" font-size="9" font-family="monospace">{lbl}</text>')

    # X-axis tick labels for strike and current price
    x_ticks = (f'<text x="{strike_x:.1f}" y="{H - 5}" text-anchor="middle" '
               f'fill="#f59e0b" font-size="9">K=${strike:.0f}</text>')
    if abs(curr_x - strike_x) > 18:
        x_ticks += (f'<text x="{curr_x:.1f}" y="{H - 5}" text-anchor="middle" '
                    f'fill="#cbd5e1" font-size="9">${current_price:.2f}</text>')

    # Breakeven label (above the line if space allows)
    be_lbl_y = pt + 10 if be_x > pl + pw * 0.4 else H - pb - 4
    be_lbl = (f'<text x="{be_x:.1f}" y="{be_lbl_y}" text-anchor="middle" '
              f'fill="{col}" font-size="8" opacity="0.8">BE=${be:.2f}</text>')

    # Legend (top-left inside chart)
    legend = (f'<text x="{pl + 4}" y="{pt + 9}" fill="#94a3b8" font-size="8">'
              f'&#x2500;&#x2500; K &nbsp; - - now &nbsp; &#xB7;&#xB7;&#xB7; BE</text>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
        f'<rect width="{W}" height="{H}" fill="#0f172a" rx="6"/>'
        # fills
        f'<polygon points="{_pp(loss_pts)}" fill="#ef4444" opacity="0.13"/>'
        f'<polygon points="{_pp(gain_pts)}" fill="#22c55e" opacity="0.16"/>'
        # axes
        f'<line x1="{pl}" y1="{zero_y:.1f}" x2="{pl+pw}" y2="{zero_y:.1f}"'
        f' stroke="#334155" stroke-width="1"/>'
        f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{H-pb}"'
        f' stroke="#334155" stroke-width="1"/>'
        # payoff curve
        f'<polyline points="{poly}" fill="none" stroke="{col}"'
        f' stroke-width="2" stroke-linejoin="round"/>'
        # strike (yellow dashes)
        f'<line x1="{strike_x:.1f}" y1="{pt}" x2="{strike_x:.1f}" y2="{H-pb}"'
        f' stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4,3"/>'
        # current price (white dashes)
        f'<line x1="{curr_x:.1f}" y1="{pt}" x2="{curr_x:.1f}" y2="{H-pb}"'
        f' stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2,4" opacity="0.75"/>'
        # breakeven (colour dashes, faint)
        f'<line x1="{be_x:.1f}" y1="{pt}" x2="{be_x:.1f}" y2="{H-pb}"'
        f' stroke="{col}" stroke-width="1" stroke-dasharray="2,3" opacity="0.55"/>'
        f'{y_ticks}{x_ticks}{be_lbl}{legend}'
        f'</svg>'
    )


def build_options_email(new_recs: list[dict]) -> str:
    """Build a rich HTML email for newly-appeared options recommendations."""
    now   = datetime.now().strftime("%Y-%m-%d %H:%M")
    syms  = sorted({r.get("symbol", "") for r in new_recs})
    calls = [r for r in new_recs if r.get("type", "").upper() == "CALL"]
    puts  = [r for r in new_recs if r.get("type", "").upper() == "PUT"]

    NCOLS = 11   # number of columns in the data table

    def _rows(r: dict, bg: str) -> str:
        """Return two <tr>: the data row + a full-width payoff chart row."""
        opt_t    = r.get("type", "").upper()
        color    = "#16a34a" if opt_t == "CALL" else "#dc2626"
        iv_pct   = f"{r.get('iv', 0) * 100:.0f}%"
        score    = r.get("score", 0)
        score_bg = "#166534" if score >= 70 else "#1e40af" if score >= 50 else "#475569"

        data_row = (
            f'<tr style="background:{bg}">'
            f'<td style="padding:10px 12px;font-weight:bold">{r.get("symbol","")}</td>'
            f'<td style="padding:10px 12px;text-align:center">'
            f'<span style="background:{color};color:white;padding:2px 8px;'
            f'border-radius:4px;font-size:12px;font-weight:bold">{opt_t}</span></td>'
            f'<td style="padding:10px 12px;text-align:right">${r.get("current_price",0):.2f}</td>'
            f'<td style="padding:10px 12px;text-align:right">${r.get("strike",0):.2f}</td>'
            f'<td style="padding:10px 12px;text-align:right">'
            f'{r.get("expiry","")} <span style="color:#94a3b8">({r.get("days_out",0)}d)</span></td>'
            f'<td style="padding:10px 12px;text-align:right">'
            f'${r.get("bid",0):.2f}&nbsp;/&nbsp;${r.get("ask",0):.2f}</td>'
            f'<td style="padding:10px 12px;text-align:right">{iv_pct}</td>'
            f'<td style="padding:10px 12px;text-align:right">{int(r.get("open_interest",0)):,}</td>'
            f'<td style="padding:10px 12px;text-align:right">{int(r.get("volume",0)):,}</td>'
            f'<td style="padding:10px 12px;text-align:center">'
            f'<span style="background:{score_bg};color:white;padding:2px 8px;'
            f'border-radius:4px;font-weight:bold">{score:.0f}</span></td>'
            f'<td style="padding:10px 12px;color:#64748b;font-size:13px">'
            f'{r.get("reason","")}</td>'
            f'</tr>'
        )

        svg = _payoff_svg(
            opt_t,
            float(r.get("strike", 0)),
            float(r.get("current_price", 0)),
            float(r.get("bid", 0)),
            float(r.get("ask", 0)),
        )
        chart_row = (
            f'<tr style="background:#111827;border-bottom:2px solid #1e293b">'
            f'<td colspan="{NCOLS}" style="padding:10px 16px 12px">'
            f'<div style="font-size:10px;color:#64748b;margin-bottom:4px">'
            f'Payoff at expiry &mdash; '
            f'<span style="color:#f59e0b">&#x2015;&#x2015; strike</span> &nbsp; '
            f'<span style="color:#e2e8f0">- - current price</span> &nbsp; '
            f'<span style="color:{"#16a34a" if opt_t=="CALL" else "#dc2626"}">'
            f'&middot;&middot;&middot; breakeven</span>'
            f'</div>'
            f'{svg}'
            f'</td></tr>'
        )
        return data_row + chart_row

    _THEAD = (
        f'<tr style="background:#1e3a8a;color:white;font-size:12px">'
        f'<th style="padding:8px 12px;text-align:left">Symbol</th>'
        f'<th style="padding:8px 12px;text-align:center">Type</th>'
        f'<th style="padding:8px 12px;text-align:right">Stock&nbsp;Price</th>'
        f'<th style="padding:8px 12px;text-align:right">Strike</th>'
        f'<th style="padding:8px 12px;text-align:right">Expiry</th>'
        f'<th style="padding:8px 12px;text-align:right">Bid&nbsp;/&nbsp;Ask</th>'
        f'<th style="padding:8px 12px;text-align:right">IV</th>'
        f'<th style="padding:8px 12px;text-align:right">OI</th>'
        f'<th style="padding:8px 12px;text-align:right">Vol</th>'
        f'<th style="padding:8px 12px;text-align:center">Score</th>'
        f'<th style="padding:8px 12px;text-align:left">Signal Reason</th>'
        f'</tr>'
    )

    def _section(recs: list[dict], title: str, color: str, emoji: str) -> str:
        if not recs:
            return ""
        rows = "".join(_rows(r, "#fff" if i % 2 == 0 else "#f1f5f9")
                       for i, r in enumerate(recs))
        return (
            f'<h3 style="color:{color};margin:24px 0 8px">'
            f'{emoji} {title} &mdash; {len(recs)} new</h3>'
            f'<table border="0" cellspacing="0" cellpadding="0" '
            f'style="border-collapse:collapse;width:100%;border-radius:12px;'
            f'overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.12)">'
            f'{_THEAD}{rows}</table>'
        )

    calls_html = _section(calls, "CALL Recommendations", "#16a34a", "&#x1F4C8;")
    puts_html  = _section(puts,  "PUT Recommendations",  "#dc2626", "&#x1F4C9;")

    return f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                   max-width:1000px;margin:auto;background:#f8fafc;padding:24px">
<div style="background:linear-gradient(135deg,#020617,#1e1b4b);color:white;
            border-radius:16px;padding:28px 32px;margin-bottom:24px">
  <h2 style="margin:0 0 4px">&#x1F4CA; New Options Recommendations</h2>
  <p style="margin:0;opacity:.7;font-size:14px">
    {now} &bull; {len(new_recs)} new signal{'s' if len(new_recs) != 1 else ''} for {', '.join(syms)}
  </p>
</div>

{calls_html}
{puts_html}

<div style="margin-top:24px;padding:16px;background:white;border-radius:12px;
            border-left:4px solid #3b82f6;box-shadow:0 1px 3px rgba(0,0,0,.08)">
  <p style="margin:0;font-size:13px;color:#64748b">
    &#x2139;&#xFE0F; <strong>Scores</strong> (0&ndash;100) reflect liquidity and strike placement.
    View live &rarr; <a href="https://jpstocktracker.pro/#options"
                        style="color:#3b82f6">jpstocktracker.pro</a>.
    Not financial advice.
  </p>
</div>

<p style="color:#94a3b8;font-size:12px;margin-top:24px;text-align:center">
  Stock Tracker &bull; {now} &bull; Unsubscribe via your alert settings
</p>
</body></html>"""


def send_options_alert(new_recs: list[dict], config: dict) -> int:
    """
    Email subscribers (and admin) about newly-appeared options recommendations.
    Returns number of subscriber emails sent.
    """
    if not _can_send(config) or not new_recs:
        return 0

    syms    = sorted({r.get("symbol", "") for r in new_recs})
    subject = f"&#x1F4CA; New Options Signals: {', '.join(syms)}"
    html    = build_options_email(new_recs)

    # Always notify admin
    send_email(subject, html, config)

    # Fan out to subscribers who track any of the relevant symbols
    sent = send_to_subscribers(subject, html, set(syms), config)
    print(f"[options alert] emailed admin + {sent} subscriber(s) — {len(new_recs)} new recs")
    return sent


def check_and_fire_alerts(stocks: list[dict], earnings: list[dict],
                          predictions: dict, config: dict) -> list[dict]:
    alert_cfg = config.get("alerts", {})
    price_thresh  = alert_cfg.get("price_change_threshold", 3.0)
    rsi_ob        = alert_cfg.get("rsi_overbought", 70)
    rsi_os        = alert_cfg.get("rsi_oversold", 30)
    earn_days     = alert_cfg.get("earnings_alert_days", 3)
    ml_thresh     = alert_cfg.get("ml_confidence_threshold", 0.70)
    vol_spike     = alert_cfg.get("volume_spike_ratio", 2.0)

    new_alerts: list[dict] = []

    for s in stocks:
        sym  = s["symbol"]
        chg  = s.get("change_pct") or 0
        rsi  = s.get("rsi")
        vol_ratio = (s.get("volume") or 0) / max(s.get("avg_volume") or 1, 1)

        if abs(chg) >= price_thresh:
            direction = "surged" if chg > 0 else "dropped"
            msg = f"{sym} {direction} {chg:+.2f}% today"
            severity = "HIGH" if abs(chg) >= price_thresh * 1.5 else "MEDIUM"
            if not db.was_alert_sent_today(f"PRICE_{direction.upper()}", sym):
                db.log_alert(f"PRICE_{direction.upper()}", sym, msg, severity)
                new_alerts.append({"symbol": sym, "message": msg, "severity": severity})

        if rsi is not None:
            if rsi <= rsi_os and not db.was_alert_sent_today("RSI_OVERSOLD", sym):
                msg = f"{sym} RSI={rsi:.0f} -- oversold, potential bounce"
                db.log_alert("RSI_OVERSOLD", sym, msg, "MEDIUM")
                new_alerts.append({"symbol": sym, "message": msg, "severity": "MEDIUM"})
            elif rsi >= rsi_ob and not db.was_alert_sent_today("RSI_OVERBOUGHT", sym):
                msg = f"{sym} RSI={rsi:.0f} -- overbought, potential pullback"
                db.log_alert("RSI_OVERBOUGHT", sym, msg, "MEDIUM")
                new_alerts.append({"symbol": sym, "message": msg, "severity": "MEDIUM"})

        if vol_ratio >= vol_spike and not db.was_alert_sent_today("VOLUME_SPIKE", sym):
            msg = f"{sym} volume spike {vol_ratio:.1f}x avg -- unusual activity"
            db.log_alert("VOLUME_SPIKE", sym, msg, "MEDIUM")
            new_alerts.append({"symbol": sym, "message": msg, "severity": "MEDIUM"})

        pred   = predictions.get(sym, {})
        conf   = pred.get("confidence", 0)
        signal = pred.get("signal", "NEUTRAL")
        if conf >= ml_thresh and signal != "NEUTRAL" and not db.was_alert_sent_today(f"ML_{signal}", sym):
            msg = f"{sym} high-confidence {signal} signal ({conf*100:.0f}%)"
            db.log_alert(f"ML_{signal}", sym, msg, "HIGH")
            new_alerts.append({"symbol": sym, "message": msg, "severity": "HIGH"})

    for e in earnings:
        sym  = e["symbol"]
        days = e.get("days_until", 99)
        if 0 <= days <= earn_days and not db.was_alert_sent_today("EARNINGS_UPCOMING", sym):
            rxn = e.get("avg_reaction_pct")
            rxn_str = f" | Avg reaction: {rxn:+.1f}%" if rxn is not None else ""
            msg = f"{sym} earnings in {days} day(s) -- {e['earnings_date']}{rxn_str}"
            db.log_alert("EARNINGS_UPCOMING", sym, msg, "HIGH")
            new_alerts.append({"symbol": sym, "message": msg, "severity": "HIGH"})

    if new_alerts:
        stocks_full   = db.get_all_stocks()
        earn_full     = db.get_upcoming_earnings()
        all_alerts    = db.get_recent_alerts(20)
        html          = build_email_report(stocks_full, earn_full, all_alerts)
        alerted_syms  = set(a["symbol"] for a in new_alerts)
        subject       = f"Stock Alert: {', '.join(sorted(alerted_syms))}"

        send_email(subject, html, config)
        send_to_subscribers(subject, html, alerted_syms, config)

        # SMS fanout
        sms_msg = subject + " -- check your email for details."
        sms_mod.send_sms_to_subscribers(sms_msg, alerted_syms, config)

    return new_alerts
