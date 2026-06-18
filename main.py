#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore")

import threading
import time
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tracker import config as cfg_mod
from tracker import database as db
from tracker import data as fetcher
from tracker import indicators as ind
from tracker import earnings as earn_mod
from tracker import predictor as pred_mod
from tracker import alerts as alert_mod
from tracker import sectors as sec_mod
from tracker import knowledge as kb_mod
from tracker import social as social_mod
from tracker import sms as sms_mod
from tracker import options as opt_mod
from tracker import sweeps as sweeps_mod
from tracker import supply_demand as sd_mod
from tracker import crypto_intel as crypto_mod
from tracker import ngx_intel as ngx_mod

console = Console()


# ── SPX / market-context helper ───────────────────────────────────────────────
def _compute_market_context(spy_hist, vix_price: float, spy_price: float,
                             spy_change: float) -> dict:
    """
    5-level market regime from SPY MA20/MA50 + VIX.
    regime_score: ±2.0 (strong) or ±1.0 (normal) or 0.0 (neutral).
    """
    ma20 = ma50 = 0.0
    try:
        if spy_hist is not None and not spy_hist.empty:
            closes = spy_hist["Close"].dropna()
            if len(closes) >= 20:
                ma20 = float(closes.tail(20).mean())
            if len(closes) >= 50:
                ma50 = float(closes.tail(50).mean())
    except Exception:
        pass

    regime_score, regime_label = 0.0, "neutral"
    if spy_price and ma20:
        d20 = (spy_price - ma20) / ma20
        d50 = ((spy_price - ma50) / ma50) if ma50 else 0.0
        if d20 > 0.01:
            if d50 > 0.02:
                regime_score, regime_label = 2.0, "strong bull"
            else:
                regime_score, regime_label = 1.0, "bull"
        elif d20 < -0.01:
            if d50 < -0.02:
                regime_score, regime_label = -2.0, "strong bear"
            else:
                regime_score, regime_label = -1.0, "bear"

    if vix_price >= 35:
        vix_label = "extreme fear"
    elif vix_price >= 25:
        vix_label = "elevated"
    elif vix_price >= 18:
        vix_label = "normal"
    elif vix_price > 0:
        vix_label = "low"
    else:
        vix_label = "unknown"

    return {
        "regime_score":  regime_score,
        "regime_label":  regime_label,
        "vix":           round(vix_price, 2),
        "vix_label":     vix_label,
        "spy_price":     spy_price,
        "spy_change":    spy_change,
        "spy_ma20":      round(ma20, 2),
        "spy_ma50":      round(ma50, 2),
    }


# ── shared state ──────────────────────────────────────────────────────────────
_state: dict = {
    "stocks": [],
    "earnings": [],
    "alerts": [],
    "predictions": {},
    "last_refresh": None,
    "refreshing": False,
    "market_open": False,
    "market_context": {},
}

_last_trained: float = 0.0  # epoch timestamp of last model training run
_RETRAIN_DAYS: int   = 7    # retrain advanced model weekly


# ── market hours ──────────────────────────────────────────────────────────────
def _is_market_open() -> bool:
    try:
        from zoneinfo import ZoneInfo
        et = ZoneInfo("America/New_York")
        now = datetime.now(et)
        if now.weekday() >= 5:
            return False
        open_t = now.replace(hour=9, minute=30, second=0, microsecond=0)
        close_t = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return open_t <= now <= close_t
    except Exception:
        return True  # assume open if timezone check fails


# ── data refresh ──────────────────────────────────────────────────────────────
def refresh_all(config: dict) -> None:
    if _state["refreshing"]:
        return
    _state["refreshing"] = True
    try:
        import random as _random
        watchlist = list(config["watchlist"])
        print(f"[refresh] starting — {len(watchlist)} symbols", flush=True)
        # Prioritise stocks not yet in DB so newly added stocks always get fetched first
        _db_syms   = {s["symbol"] for s in db.get_all_stocks()}
        _missing   = [s for s in watchlist if s not in _db_syms]
        _present   = [s for s in watchlist if s in _db_syms]
        _random.shuffle(_missing)
        _random.shuffle(_present)
        watchlist  = _missing + _present   # missing first, then random rotation
        if _missing:
            print(f"[refresh] prioritising {len(_missing)} unloaded stocks: {_missing}", flush=True)
        print(f"[refresh] fetching snapshots...", flush=True)
        snaps = fetcher.fetch_multiple_snapshots(watchlist)
        print(f"[refresh] snapshots done — {len(snaps)} returned", flush=True)

        # Pre-fetch SPY history + VIX for market context (cached on repeat calls)
        _spy_hist  = fetcher.fetch_history("SPY", period="2y")
        _vix_snap  = fetcher.fetch_ticker_snapshot("^VIX")
        _vix_price = float((_vix_snap or {}).get("price") or 0.0)
        _spy_snap  = snaps.get("SPY") or {}
        _spy_price = float(_spy_snap.get("price") or 0.0)
        _spy_chg   = float(_spy_snap.get("change_pct") or 0.0)

        # Pre-fetch BTC history + crypto external APIs (cached, non-blocking on error)
        _btc_hist  = fetcher.fetch_history("BTC-USD", period="2y")
        _btc_snap  = snaps.get("BTC-USD") or {}
        _btc_price = float(_btc_snap.get("price") or 0.0)
        _fear_greed    = crypto_mod.fetch_fear_greed()
        _btc_dominance = crypto_mod.fetch_btc_dominance()
        _btc_regime    = crypto_mod.compute_btc_regime(_btc_hist, _btc_price)

        stocks_out = []
        predictions_out = {}
        hist_data  = {}
        all_hists  = {}   # collected for ML training
        earnings_map = {e["symbol"]: e["days_until"] for e in _state["earnings"]}

        market_context = _compute_market_context(
            _spy_hist, _vix_price, _spy_price, _spy_chg
        )
        market_regime = market_context["regime_score"]

        for _i, sym in enumerate(watchlist):
            if _i > 0 and _i % 50 == 0:
                print(f"[refresh] progress {_i}/{len(watchlist)} stocks processed", flush=True)
            try:
                snap = snaps.get(sym)
                if not snap:
                    continue
                hist = fetcher.fetch_history(sym, period="2y")
                if hist is None or len(hist) < 30:
                    print(f"[refresh] {sym}: skipped — hist={'None' if hist is None else len(hist)} rows")
                    continue
                hist_data[sym] = snap
                hist_data[sym]["hist"] = hist
                if len(hist) >= 80:
                    all_hists[sym] = hist

                ind_data = ind.get_latest_indicators(hist)
                days_to_earn = earnings_map.get(sym)
                prediction = pred_mod.generate_prediction(
                    sym, ind_data, snap, days_to_earn,
                    market_regime=market_regime,
                    vix=market_context.get("vix") or 0.0
                )
                # NGX/LSE low-liquidity confidence adjustment
                if sym.endswith(".L"):
                    prediction["confidence"] = round(
                        ngx_mod.ngx_liquidity_adjust(prediction["confidence"], sym), 2
                    )
                predictions_out[sym] = prediction

                sector = sec_mod.resolve_sector(sym, config.get("stock_sectors", {}))
                _fib = ind_data.get("fib_levels", {})
                uptrend_prob = pred_mod.get_uptrend_probability(ind_data)

                # Supply & demand zones from volume profile (free — uses existing hist)
                _sd  = sd_mod.volume_zones(hist, snap["price"])
                stock_row = {
                    "symbol": sym,
                    "price": snap["price"],
                    "prev_close": snap["prev_close"],
                    "change_pct": snap["change_pct"],
                    "volume": snap["volume"],
                    "avg_volume": snap["avg_volume"],
                    "rsi": ind_data["rsi"],
                    "macd": ind_data["macd"],
                    "macd_signal": ind_data["macd_signal"],
                    "bb_pband": ind_data["bb_pband"],
                    "ma20": ind_data["ma20"],
                    "ma50": ind_data["ma50"],
                    "ma200": ind_data["ma200"],
                    "prediction": prediction["signal"],
                    "prediction_confidence": prediction["confidence"],
                    "rule_signals": [s["name"] for s in prediction["rule_signals"]],
                    "sector": sector,
                    "fib_signal": int(_fib.get("signal", 0)),
                    "fib_level":  _fib.get("signal_level", ""),
                    "uptrend_prob": uptrend_prob,
                    "demand_zone": _sd["demand"][0]["price"] if _sd["demand"] else None,
                    "supply_zone": _sd["supply"][0]["price"] if _sd["supply"] else None,
                    "poc_price":   _sd.get("poc"),
                    "btc_corr": (
                        crypto_mod.btc_correlation(hist, _btc_hist)
                        if sec_mod.is_crypto(sym) and sym != "BTC-USD"
                        else (1.0 if sym == "BTC-USD" else None)
                    ),
                    # Extra indicator fields passed in-memory to alerts (not stored in DB)
                    "macd_hist":         ind_data.get("macd_hist"),
                    "obv_roc_5d":        ind_data.get("obv_roc_5d"),
                    "adx":               ind_data.get("adx"),
                    "pct_from_52w_high": ind_data.get("pct_from_52w_high"),
                    "pct_from_52w_low":  ind_data.get("pct_from_52w_low"),
                }
                db.upsert_stock(stock_row)
                stocks_out.append(stock_row)
                if sym == "NVTS":
                    print(f"[refresh] NVTS: ✓ upsert complete, price={stock_row.get('price')}")
            except Exception as _e:
                print(f"[refresh] {sym}: exception — {_e}")

        # ── Watchlist breadth: % of equity stocks above MA50 ──────────────────
        _eq = [s for s in stocks_out
               if not sec_mod.is_crypto(s["symbol"])
               and s.get("price") and s.get("ma50")]
        _breadth_above = sum(1 for s in _eq if s["price"] > s["ma50"])
        _breadth_total = len(_eq)
        _breadth_pct   = round(_breadth_above / _breadth_total * 100, 1) if _breadth_total else 0.0

        # ── Sector relative strength vs SPY today ─────────────────────────────
        _sect_chgs: dict[str, list] = {}
        for _s in stocks_out:
            if not sec_mod.is_crypto(_s["symbol"]) and _s.get("change_pct") is not None:
                _sect = _s.get("sector") or "General"
                _sect_chgs.setdefault(_sect, []).append(_s["change_pct"])
        _sector_strength = {
            sect: round(sum(chgs) / len(chgs) - market_context.get("spy_change", 0.0), 2)
            for sect, chgs in _sect_chgs.items() if chgs
        }

        market_context.update({
            "breadth_pct":     _breadth_pct,
            "breadth_above":   _breadth_above,
            "breadth_total":   _breadth_total,
            "sector_strength": _sector_strength,
        })
        _state["market_context"] = market_context
        try:
            import json as _mcjson
            db.set_kv("market_context", _mcjson.dumps(market_context))
        except Exception:
            pass

        # ── Crypto context ────────────────────────────────────────────────────
        print(f"[refresh] computing crypto/NGX context...", flush=True)
        _crypto_stocks = [s for s in stocks_out if sec_mod.is_crypto(s["symbol"])]
        _crypto_correlations = {
            s["symbol"]: s.get("btc_corr")
            for s in _crypto_stocks
            if s.get("btc_corr") is not None
        }
        crypto_context = {
            "fear_greed":   _fear_greed,
            "btc_dominance": _btc_dominance,
            "btc_regime":   _btc_regime,
            "btc_price":    _btc_price,
            "correlations": _crypto_correlations,
        }
        try:
            import json as _cjson
            db.set_kv("crypto_context", _cjson.dumps(crypto_context))
            print(f"[refresh] crypto_context saved — fg={_fear_greed.get('value')} btcdom={_btc_dominance.get('btc')} regime={_btc_regime.get('label')} corrs={len(_crypto_correlations)}", flush=True)
        except Exception as _ce:
            print(f"[refresh] crypto_context ERROR: {_ce}", flush=True)

        # ── NGX context ───────────────────────────────────────────────────────
        _ngx_stocks = [
            s for s in stocks_out
            if s["symbol"].endswith(".L") or
               sec_mod.resolve_sector(s["symbol"], config.get("stock_sectors", {}))
               == "Nigerian Exchange (NGX)"
        ]
        ngx_context = ngx_mod.compute_ngx_context(_ngx_stocks)
        ngx_context["usdngn"]     = ngx_mod.fetch_usdngn()
        ngx_context["mkt_status"] = ngx_mod.ngx_market_status()
        try:
            import json as _njson
            db.set_kv("ngx_context", _njson.dumps(ngx_context))
            print(f"[refresh] ngx_context saved — ngx_stocks={len(_ngx_stocks)} rate={ngx_context['usdngn'].get('rate')} open={ngx_context['mkt_status'].get('is_open')}", flush=True)
        except Exception as _ne:
            print(f"[refresh] ngx_context ERROR: {_ne}", flush=True)

        earnings_list = earn_mod.refresh_earnings_calendar(watchlist, hist_data)
        new_alerts = alert_mod.check_and_fire_alerts(
            stocks_out, earnings_list, predictions_out, config,
            market_regime=market_regime, market_context=market_context
        )

        # ── Prediction accuracy tracking ──────────────────────────────────────
        # Log today's predictions and score any that are 5+ trading days old
        current_prices = {s["symbol"]: s["price"] for s in stocks_out if s.get("price")}
        try:
            for sym, pred in predictions_out.items():
                price = current_prices.get(sym)
                if price:
                    db.log_prediction(
                        sym, pred["signal"], pred["confidence"],
                        pred["combined_prob"], price
                    )
            db.score_pending_predictions(current_prices, score_after_days=5)
        except Exception:
            pass

        _state["stocks"] = stocks_out
        _state["earnings"] = earnings_list
        _state["predictions"] = predictions_out
        _state["alerts"] = db.get_recent_alerts(8)
        _state["last_refresh"] = datetime.now()
        _state["market_open"] = _is_market_open()

        # ── Options intelligence refresh ──────────────────────────────────────
        try:
            _refresh_options(stocks_out, config)
        except Exception:
            pass

        # ── Sweeps / dark pool refresh ────────────────────────────────────────
        try:
            _refresh_sweeps(stocks_out, config)
        except Exception:
            pass

        # ── Auto-train advanced ML model (background thread) ─────────────────
        # Trains on first startup if advanced_model.pkl is missing, then weekly.
        global _last_trained
        _adv_missing = not pred_mod.ADV_MODEL_PATH.exists()
        _stale       = time.time() - _last_trained > _RETRAIN_DAYS * 86400
        if (_adv_missing or _stale) and len(all_hists) >= 50:
            _last_trained = time.time()
            _hists_snap   = dict(all_hists)
            print(f"[refresh] spawning ML training — {len(_hists_snap)} stocks", flush=True)
            def _do_train(h=_hists_snap):
                try:
                    pred_mod.train_model(h)
                except Exception as _te:
                    print(f"[train] error: {_te}", flush=True)
            threading.Thread(target=_do_train, daemon=True).start()
    finally:
        _state["refreshing"] = False


def _refresh_options(stocks: list[dict], config: dict) -> None:
    """
    Fetch and score options for the top high-signal stocks.
    Only runs for BULLISH/BEARISH signals with confidence >= 30%
    on optionable (non-crypto, price >= $5) symbols.
    Emails subscribers when new contracts appear that weren't in the previous batch.
    """
    MIN_CONF = 0.30   # works with rule-based signals; ML model raises this naturally

    all_signals = [s for s in stocks if s.get("prediction") in ("BULLISH", "BEARISH")]
    candidates  = [
        s for s in all_signals
        if (s.get("prediction_confidence") or 0) >= MIN_CONF
        and opt_mod.is_optionable(s["symbol"], s.get("price") or 0)
    ]

    print(f"[options] {len(all_signals)} BULL/BEAR signals, {len(candidates)} optionable ≥{MIN_CONF*100:.0f}% conf")

    # Snapshot the current DB recs BEFORE clearing — used to detect new arrivals
    prev_recs = db.get_option_recs(40)
    prev_keys = {
        (r["symbol"], r["opt_type"], float(r["strike"]), r["expiry"])
        for r in prev_recs
    }

    # Rank by confidence, analyse top 20 to keep refresh time reasonable
    candidates.sort(key=lambda s: s.get("prediction_confidence") or 0, reverse=True)
    candidates = candidates[:20]

    all_recs: list[dict] = []
    for s in candidates:
        try:
            recs = opt_mod.get_recommendations(
                symbol=s["symbol"],
                price=s["price"],
                prediction=s["prediction"],
                confidence=s["prediction_confidence"],
                rsi=s.get("rsi"),
                macd=s.get("macd"),
                change_pct=s.get("change_pct"),
                fib_signal=s.get("fib_signal", 0),
                fib_level=s.get("fib_level", ""),
            )
            if recs:
                print(f"[options] {s['symbol']} → {len(recs)} {s['prediction']} recs (score {recs[0]['score']:.0f})")
            else:
                print(f"[options] {s['symbol']} conf={s.get('prediction_confidence',0):.2f} {s.get('prediction')} → no recs")
            all_recs.extend(recs)
        except Exception as e:
            print(f"[options] {s['symbol']} error: {e}")
        time.sleep(0.15)

    print(f"[options] total recommendations: {len(all_recs)}")

    # Keep top 30 by score, clear old, store new
    all_recs.sort(key=lambda r: r["score"], reverse=True)
    top_recs = all_recs[:30]
    db.clear_option_recs()
    db.upsert_option_recs(top_recs)

    # Compute OI levels (call wall / put wall / max pain) for each analysed symbol
    oi_levels: dict = {}
    for s in candidates[:15]:
        try:
            chain = opt_mod.fetch_option_chain(s["symbol"])
            if chain:
                levels = sd_mod.options_oi_levels(chain)
                levels["price"] = s.get("price")
                oi_levels[s["symbol"]] = levels
        except Exception:
            pass
    try:
        import json as _oijson
        db.set_kv("oi_levels", _oijson.dumps(oi_levels))
    except Exception:
        pass

    # ── Email alert for genuinely new contracts ────────────────────────────────
    truly_new = []
    for r in top_recs:
        key        = (r["symbol"], r["type"], float(r["strike"]), r["expiry"])
        alert_type = f"OPTIONS_{r['type']}"       # OPTIONS_CALL or OPTIONS_PUT
        alert_sym  = f"{r['symbol']}_{r['strike']}_{r['expiry']}"
        if key not in prev_keys and not db.was_alert_sent_today(alert_type, alert_sym):
            truly_new.append(r)
            db.log_alert(alert_type, alert_sym,
                         f"{r['type']} {r['symbol']} ${r['strike']} exp {r['expiry']} score={r['score']:.0f}",
                         "HIGH")

    if truly_new:
        print(f"[options alert] {len(truly_new)} new contract(s) — firing email")
        try:
            alert_mod.send_options_alert(truly_new, config)
        except Exception as e:
            print(f"[options alert] email error: {e}")


def _refresh_sweeps(stocks: list[dict], config: dict) -> None:
    """Scan for options sweeps, golden sweeps, and dark pool block activity."""
    watchlist  = config.get("watchlist", [])
    stocks_db  = {s["symbol"]: s for s in stocks}
    counts     = sweeps_mod.refresh_sweeps(watchlist, stocks_db)
    print(f"[sweeps] golden={counts['golden']}  opts={counts['opts']}  dark_pool={counts['dark_pool']}")

    # Alert on golden sweeps and significant dark pool blocks
    from tracker import database as _db
    sweep_data = _db.get_all_sweeps_today()
    alertable  = sweep_data["golden"] + [
        b for b in sweep_data["dark_pool"] if (b.get("notional") or 0) >= 5_000_000
    ]
    truly_new = []
    for s in alertable:
        atype = f"SWEEP_{s['sweep_type']}"
        asym  = f"{s['symbol']}_{s.get('expiry','') or s.get('created_at','')[:10]}"
        if not _db.was_alert_sent_today(atype, s["symbol"]):
            truly_new.append(s)
            _db.log_alert(atype, s["symbol"],
                          f"{s['sweep_type']} {s['symbol']} premium=${s.get('total_premium',0):,.0f} notional=${s.get('notional',0):,.0f}",
                          "HIGH")
    if truly_new:
        print(f"[sweeps] firing alert for {len(truly_new)} new sweep(s)")
        try:
            alert_mod.send_sweep_alert(truly_new, config)
        except Exception as e:
            print(f"[sweeps alert] error: {e}")


# ── dashboard renderers ───────────────────────────────────────────────────────
def _sector_strength_summary(sector_strength: dict) -> str:
    if not sector_strength:
        return ""
    ranked = sorted(sector_strength.items(), key=lambda x: x[1], reverse=True)
    top = [(s, v) for s, v in ranked[:2] if v > 0]
    bot = [(s, v) for s, v in ranked[-2:] if v < 0]
    parts = []
    for s, v in top:
        short = s.split(" & ")[0].split("/")[0][:12]
        parts.append(f"[green]{short} +{v:.1f}%[/green]")
    for s, v in bot:
        short = s.split(" & ")[0].split("/")[0][:12]
        parts.append(f"[red]{short} {v:.1f}%[/red]")
    return "Sectors: " + "  ".join(parts) if parts else ""


def _header_panel() -> Panel:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "[green]OPEN[/green]" if _state["market_open"] else "[red]CLOSED[/red]"
    last = _state["last_refresh"].strftime("%H:%M:%S") if _state["last_refresh"] else "never"
    spin = "[yellow]...[/yellow]" if _state["refreshing"] else ""

    mctx         = _state.get("market_context") or {}
    regime_label = mctx.get("regime_label", "")
    vix          = mctx.get("vix") or 0.0
    vix_label    = mctx.get("vix_label", "")
    breadth_pct  = mctx.get("breadth_pct", 0.0)
    breadth_tot  = mctx.get("breadth_total", 0)

    _REGIME_COLOR = {
        "strong bull": "bright_green", "bull": "green",
        "neutral": "yellow",
        "bear": "red", "strong bear": "bright_red",
    }
    _VIX_COLOR = ("bright_red" if vix >= 35 else "red" if vix >= 25
                  else "yellow" if vix >= 18 else "green")
    _BREADTH_COLOR = "green" if breadth_pct >= 60 else "red" if breadth_pct < 40 else "yellow"

    txt = Text.assemble(
        ("  STOCK TRACKER  ", "bold white on blue"),
        f"   {now}   Market: ", status,
        f"   Last update: {last} ", spin,
    )
    if regime_label:
        txt.append("\n  SPX: ", "dim white")
        txt.append(regime_label.upper(), f"bold {_REGIME_COLOR.get(regime_label, 'white')}")
        txt.append("   VIX: ", "dim white")
        vix_str = f"{vix:.1f} ({vix_label})" if vix else "—"
        txt.append(vix_str, f"bold {_VIX_COLOR}")
        if breadth_tot:
            txt.append("   Breadth: ", "dim white")
            txt.append(f"{breadth_pct:.0f}% above MA50 ({breadth_tot} stocks)",
                       f"bold {_BREADTH_COLOR}")

        sect_str = _sector_strength_summary(mctx.get("sector_strength") or {})
        if sect_str:
            txt.append(f"\n  {sect_str}", "dim white")

    return Panel(txt, style="blue")


def _sig_color(sig: Optional[str]) -> str:
    return {"BULLISH": "green", "BEARISH": "red"}.get(sig or "", "yellow")


def _stocks_table() -> Table:
    table = Table(
        title="Watchlist by Sector",
        show_header=True,
        header_style="bold white on dark_blue",
        border_style="blue",
        expand=True,
    )
    table.add_column("Symbol", style="bold", width=7)
    table.add_column("Price", justify="right", width=9)
    table.add_column("Chg %", justify="right", width=8)
    table.add_column("Vol", justify="right", width=8)
    table.add_column("RSI", justify="center", width=6)
    table.add_column("vs MA50", justify="center", width=8)
    table.add_column("Signal", justify="center", width=10)
    table.add_column("Conf", justify="right", width=6)
    table.add_column("Top Signal", width=26)

    stocks = _state["stocks"]
    if not stocks:
        table.add_row("[dim]Loading data...[/dim]", "", "", "", "", "", "", "", "")
        return table

    # group by sector preserving catalog order
    grouped: dict[str, list] = {}
    for s in stocks:
        sect = s.get("sector") or "General"
        grouped.setdefault(sect, []).append(s)

    # sort sectors: catalog order first, then alphabetical remainder
    catalog_order = list(sec_mod.SECTOR_CATALOG.keys())
    def _sect_key(name):
        return (catalog_order.index(name) if name in catalog_order else 999, name)
    sorted_sectors = sorted(grouped.keys(), key=_sect_key)

    for sector in sorted_sectors:
        color = sec_mod.get_sector_color(sector)
        # sector header row
        table.add_row(
            Text(f"  {sector}", style=f"bold {color}"),
            "", "", "", "", "", "", "", "",
            style=f"on grey15",
        )
        for s in sorted(grouped[sector], key=lambda x: x["symbol"]):
            chg = s.get("change_pct") or 0
            chg_style = "green" if chg >= 0 else "red"

            rsi = s.get("rsi")
            rsi_str = f"{rsi:.0f}" if rsi else "N/A"
            rsi_style = "red" if (rsi and rsi >= 70) else ("green" if (rsi and rsi <= 30) else "white")

            price = s.get("price") or 0
            ma50 = s.get("ma50")
            if price and ma50:
                pct_vs = (price - ma50) / ma50 * 100
                vs_str = f"{pct_vs:+.1f}%"
                vs_style = "green" if pct_vs >= 0 else "red"
            else:
                vs_str, vs_style = "N/A", "white"

            sig = s.get("prediction", "NEUTRAL")
            conf = s.get("prediction_confidence") or 0
            sig_icon = {"BULLISH": "^", "BEARISH": "v"}.get(sig, "-")

            rules = s.get("rule_signals") or []
            top_rule = rules[0][:24] if rules else ""

            vol = s.get("volume") or 0
            vol_str = f"{vol/1_000_000:.1f}M" if vol >= 1_000_000 else f"{vol/1_000:.0f}K"

            table.add_row(
                f"  {s['symbol']}",
                f"${price:.2f}",
                Text(f"{chg:+.2f}%", style=chg_style),
                vol_str,
                Text(rsi_str, style=rsi_style),
                Text(vs_str, style=vs_style),
                Text(f"{sig_icon} {sig}", style=_sig_color(sig)),
                f"{conf*100:.0f}%",
                top_rule,
            )
    return table


def _earnings_table() -> Table:
    table = Table(
        title="Upcoming Earnings",
        show_header=True,
        header_style="bold white on dark_blue",
        border_style="blue",
        expand=True,
    )
    table.add_column("Symbol", style="bold", width=8)
    table.add_column("Date", width=12)
    table.add_column("Days", justify="center", width=6)
    table.add_column("EPS Est", justify="right", width=9)
    table.add_column("Avg Reaction", justify="right", width=13)

    for e in _state["earnings"][:8]:
        days = e.get("days_until", 99)
        days_style = "red bold" if days <= 3 else ("yellow" if days <= 7 else "white")
        eps = e.get("eps_estimate")
        eps_str = f"${eps:.2f}" if eps is not None else "N/A"
        rxn = e.get("avg_reaction_pct")
        rxn_str = f"{rxn:+.1f}%" if rxn is not None else "N/A"
        rxn_style = "green" if (rxn and rxn > 0) else "red" if (rxn and rxn < 0) else "white"
        table.add_row(
            e["symbol"],
            e.get("earnings_date", ""),
            Text(str(days), style=days_style),
            eps_str,
            Text(rxn_str, style=rxn_style),
        )
    if not _state["earnings"]:
        table.add_row("[dim]No upcoming earnings[/dim]", "", "", "", "")
    return table


def _alerts_panel() -> Panel:
    alerts = _state["alerts"]
    if not alerts:
        return Panel("[dim]No alerts yet[/dim]", title="Recent Alerts", border_style="blue")

    lines = []
    for a in alerts[:6]:
        sev = a.get("severity", "LOW")
        color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(sev, "white")
        sym = a.get("symbol", "")
        msg = a.get("message", "")
        ts = (a.get("created_at") or "")[:16]
        lines.append(f"[{color}][{sev}][/{color}] [{ts}] [bold]{sym}[/bold] {msg}")

    return Panel("\n".join(lines), title="Recent Alerts", border_style="blue")


def _build_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=6),
        Layout(name="body"),
        Layout(name="alerts", size=10),
    )
    layout["body"].split_row(
        Layout(name="stocks", ratio=3),
        Layout(name="earnings", ratio=2),
    )
    return layout


# ── CLI commands ──────────────────────────────────────────────────────────────
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(dashboard)


@cli.command()
def dashboard():
    """Launch the live CLI dashboard."""
    db.init_db()
    config = cfg_mod.load_config()
    layout = _build_layout()

    # Initial data fetch in background
    threading.Thread(target=refresh_all, args=(config,), daemon=True).start()

    interval = config.get("refresh_interval", 300)
    last_full_refresh = time.time()

    console.print("[bold blue]Starting Stock Tracker...[/bold blue] Press Ctrl+C to exit.\n")
    try:
        with Live(layout, refresh_per_second=2, screen=True) as _:
            while True:
                layout["header"].update(_header_panel())
                layout["body"]["stocks"].update(Panel(_stocks_table(), border_style="blue"))
                layout["body"]["earnings"].update(Panel(_earnings_table(), border_style="blue"))
                layout["alerts"].update(_alerts_panel())

                if time.time() - last_full_refresh >= interval and not _state["refreshing"]:
                    threading.Thread(target=refresh_all, args=(config,), daemon=True).start()
                    last_full_refresh = time.time()

                time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    console.print("\n[bold]Goodbye![/bold]")


@cli.command()
@click.argument("symbols", nargs=-1, required=True)
def add(symbols):
    """Add one or more stock symbols to the watchlist."""
    config = cfg_mod.load_config()
    watchlist = config["watchlist"]
    added = []
    for sym in [s.upper() for s in symbols]:
        if sym not in watchlist:
            watchlist.append(sym)
            added.append(sym)
    config["watchlist"] = watchlist
    cfg_mod.save_config(config)
    if added:
        console.print(f"[green]Added:[/green] {', '.join(added)}")
    else:
        console.print("[yellow]All symbols already in watchlist.[/yellow]")


@cli.command()
@click.argument("symbols", nargs=-1, required=True)
def remove(symbols):
    """Remove one or more stock symbols from the watchlist."""
    config = cfg_mod.load_config()
    watchlist = config["watchlist"]
    removed = []
    for sym in [s.upper() for s in symbols]:
        if sym in watchlist:
            watchlist.remove(sym)
            removed.append(sym)
    config["watchlist"] = watchlist
    cfg_mod.save_config(config)
    if removed:
        console.print(f"[red]Removed:[/red] {', '.join(removed)}")
    else:
        console.print("[yellow]Symbols not found in watchlist.[/yellow]")


@cli.command(name="list")
def list_watchlist():
    """List current watchlist."""
    config = cfg_mod.load_config()
    watchlist = config["watchlist"]
    console.print("[bold]Current watchlist:[/bold]")
    for sym in watchlist:
        console.print(f"  • {sym}")


@cli.command()
def train():
    """Train the ML prediction model on historical data."""
    db.init_db()
    config = cfg_mod.load_config()
    watchlist = config["watchlist"]
    console.print(f"[bold]Fetching historical data for {len(watchlist)} stocks...[/bold]")

    all_hists = {}
    for sym in watchlist:
        console.print(f"  Fetching {sym}...", end=" ")
        hist = fetcher.fetch_history(sym, period="2y")
        if hist is not None and len(hist) >= 80:
            all_hists[sym] = hist
            console.print(f"[green]OK[/green] ({len(hist)} days)")
        else:
            n = len(hist) if hist is not None else 0
            console.print(f"[red]insufficient data ({n} days)[/red]")

    if not all_hists:
        console.print("[red]No data available for training.[/red]")
        return

    console.print(f"\n[bold]Training 3-model ensemble on {len(all_hists)} stocks...[/bold]")
    console.print("[dim]  Models: RandomForest + ExtraTrees + HistGradientBoosting[/dim]")
    console.print("[dim]  Target: 3-day forward return | 15 technical features[/dim]\n")

    success, feature_importance = pred_mod.train_model(all_hists)

    if success:
        meta = pred_mod.get_model_metadata()
        console.print("[green bold]Model trained successfully![/green bold]")
        console.print(f"  [dim]Samples: {meta.get('n_samples', '?'):,}  |  "
                      f"Stocks: {meta.get('n_stocks', '?')}  |  "
                      f"Features: {meta.get('n_features', '?')}[/dim]")
        console.print(f"  [dim]Model saved to models/stock_model.pkl[/dim]\n")

        if feature_importance:
            from rich.table import Table as RTable
            tbl = RTable(title="Feature Importance (RF + ExtraTrees average)",
                         border_style="blue", header_style="bold white on dark_blue")
            tbl.add_column("Feature",    style="bold", min_width=22)
            tbl.add_column("Importance", justify="right", width=12)
            tbl.add_column("Bar",        width=30)

            max_fi = max(feature_importance.values()) or 1
            for feat, fi in sorted(feature_importance.items(),
                                   key=lambda x: x[1], reverse=True):
                bar_len = int(fi / max_fi * 28)
                bar     = "[green]" + "#" * bar_len + "[/green]" + "." * (28 - bar_len)
                tbl.add_row(feat, f"{fi:.4f}", bar)
            console.print(tbl)
    else:
        console.print("[red]Training failed. Check logs.[/red]")


@cli.command()
@click.option("--detail", is_flag=True, help="Show recent individual predictions")
def accuracy(detail):
    """Show prediction accuracy statistics tracked over time."""
    db.init_db()
    stats = db.get_prediction_accuracy(min_scored=1)

    console.print()
    console.print("[bold blue]  Prediction Accuracy Report[/bold blue]")
    console.print("[dim]  Predictions scored 5+ trading days after signal[/dim]\n")

    if stats.get("insufficient_data") or stats.get("total", 0) == 0:
        console.print(f"[yellow]Not enough scored predictions yet.[/yellow]")
        console.print(f"  Scored so far: [bold]{stats.get('total', 0)}[/bold]")
        console.print("[dim]  Run the dashboard or 'report' command daily to accumulate data.[/dim]\n")
        return

    total   = stats["total"]
    acc     = stats["accuracy_pct"]
    correct = stats["correct"]
    acc_color = "green" if acc >= 55 else ("yellow" if acc >= 50 else "red")

    console.print(f"  Overall accuracy:  [{acc_color}][bold]{acc}%[/bold][/{acc_color}]"
                  f"  ({correct}/{total} scored predictions)")

    bull_acc = stats.get("bull_accuracy_pct")
    bear_acc = stats.get("bear_accuracy_pct")
    if bull_acc is not None:
        bc = "green" if bull_acc >= 55 else ("yellow" if bull_acc >= 50 else "red")
        console.print(f"  BULLISH accuracy:  [{bc}]{bull_acc}%[/{bc}]"
                      f"  ({stats['bull_total']} signals)")
    if bear_acc is not None:
        bc = "green" if bear_acc >= 55 else ("yellow" if bear_acc >= 50 else "red")
        console.print(f"  BEARISH accuracy:  [{bc}]{bear_acc}%[/{bc}]"
                      f"  ({stats['bear_total']} signals)")

    hi_acc = stats.get("hi_conf_acc_pct")
    if hi_acc is not None and stats.get("hi_conf_total", 0) >= 3:
        hc = "green" if hi_acc >= 60 else ("yellow" if hi_acc >= 50 else "red")
        console.print(f"  High-conf (>=50%): [{hc}]{hi_acc}%[/{hc}]"
                      f"  ({stats['hi_conf_total']} signals)")

    avg_ret = stats.get("avg_return_pct", 0)
    ret_color = "green" if avg_ret > 0 else "red"
    console.print(f"  Avg return (5d):   [{ret_color}]{avg_ret:+.2f}%[/{ret_color}]")

    if detail:
        rows = db.get_recent_predictions(30)
        if rows:
            from rich.table import Table as RTable
            tbl = RTable(title="Recent Predictions (newest first)",
                         border_style="blue", header_style="bold white on dark_blue")
            tbl.add_column("Date",   width=11)
            tbl.add_column("Symbol", style="bold", width=7)
            tbl.add_column("Signal", width=9)
            tbl.add_column("Conf",   justify="right", width=6)
            tbl.add_column("Entry",  justify="right", width=8)
            tbl.add_column("Exit",   justify="right", width=8)
            tbl.add_column("Return", justify="right", width=8)
            tbl.add_column("Result", justify="center", width=8)

            for r in rows:
                sig   = r.get("signal", "")
                sig_c = {"BULLISH": "green", "BEARISH": "red"}.get(sig, "yellow")
                ret   = r.get("actual_return_pct")
                ret_s = f"{ret:+.2f}%" if ret is not None else "[dim]pending[/dim]"
                ret_c = "green" if (ret or 0) > 0 else "red" if (ret or 0) < 0 else "white"

                correct = r.get("was_correct")
                if correct is None:
                    res_s = "[dim]--[/dim]"
                elif correct == 1:
                    res_s = "[green]CORRECT[/green]"
                else:
                    res_s = "[red]WRONG[/red]"

                exit_p = r.get("price_scored")
                exit_s = f"${exit_p:.2f}" if exit_p else "[dim]--[/dim]"

                tbl.add_row(
                    (r.get("prediction_date") or "")[:10],
                    r.get("symbol", ""),
                    f"[{sig_c}]{sig}[/{sig_c}]",
                    f"{(r.get('confidence') or 0)*100:.0f}%",
                    f"${r.get('price_at_prediction') or 0:.2f}",
                    exit_s,
                    Text(ret_s, style=ret_c) if ret is not None else "[dim]pending[/dim]",
                    res_s,
                )
            console.print()
            console.print(tbl)

    console.print()
    console.print("[dim]  Use --detail to see individual prediction outcomes.[/dim]\n")


@cli.command()
def setup():
    """Interactive configuration wizard (email, SMS, social media)."""
    config = cfg_mod.load_config()

    # ── Email ─────────────────────────────────────────────────────────────────
    console.print("[bold blue]== Email Setup ==[/bold blue]")
    console.print("[dim]For Gmail, use an App Password (myaccount.google.com > Security > App Passwords)[/dim]\n")

    sender = click.prompt("Sender email", default=config["email"].get("sender") or "")
    password = click.prompt("App password", hide_input=True, default="")
    recipient = click.prompt("Recipient email", default=config["email"].get("recipient") or "obiomap@gmail.com")

    config["email"]["sender"] = sender
    config["email"]["password"] = password
    config["email"]["recipient"] = recipient
    config["email"]["enabled"] = bool(sender and password)

    # ── SMS (Twilio) ──────────────────────────────────────────────────────────
    console.print("\n[bold blue]== SMS Setup (Twilio) ==[/bold blue]")
    console.print("[dim]Sign up at twilio.com for a free trial (~$15 credit). Leave blank to skip.[/dim]\n")

    twilio_sid   = click.prompt("Twilio Account SID",   default=config["sms"].get("twilio_sid", "") or "", show_default=False)
    twilio_token = click.prompt("Twilio Auth Token",     default="", hide_input=True, show_default=False)
    twilio_from  = click.prompt("Twilio From number (+1XXXXXXXXXX)", default=config["sms"].get("twilio_from", "") or "", show_default=False)

    if twilio_sid:
        config["sms"]["twilio_sid"]   = twilio_sid
        config["sms"]["twilio_token"] = twilio_token or config["sms"].get("twilio_token", "")
        config["sms"]["twilio_from"]  = twilio_from
        config["sms"]["enabled"]      = True

    # ── Twitter/X ─────────────────────────────────────────────────────────────
    console.print("\n[bold blue]== Twitter/X Setup ==[/bold blue]")
    console.print("[dim]Create an app at developer.twitter.com. Leave blank to skip.[/dim]\n")

    tw = config.get("social", {}).get("twitter", {})
    api_key      = click.prompt("API Key (Consumer Key)",    default=tw.get("api_key", "") or "", show_default=False)
    api_secret   = click.prompt("API Secret",               default="", hide_input=True, show_default=False)
    access_token = click.prompt("Access Token",             default=tw.get("access_token", "") or "", show_default=False)
    access_secret= click.prompt("Access Token Secret",      default="", hide_input=True, show_default=False)
    public_url   = click.prompt("Your public signup URL (e.g. https://your-ip:5443)",
                                default=config.get("social", {}).get("public_url", "") or "")

    if api_key:
        config.setdefault("social", {}).setdefault("twitter", {})
        config["social"]["twitter"]["api_key"]       = api_key
        config["social"]["twitter"]["api_secret"]    = api_secret or tw.get("api_secret", "")
        config["social"]["twitter"]["access_token"]  = access_token
        config["social"]["twitter"]["access_secret"] = access_secret or tw.get("access_secret", "")
        config["social"]["twitter"]["enabled"]       = True
    if public_url:
        config.setdefault("social", {})["public_url"] = public_url

    cfg_mod.save_config(config)

    console.print(f"\n[green]Configuration saved![/green]")
    console.print(f"  Email alerts -> {recipient}")
    if twilio_sid:
        console.print(f"  SMS via Twilio from {twilio_from}")
    if api_key:
        console.print(f"  Twitter/X posting enabled")
    console.print("[dim]Run 'python main.py report' to send a test report.[/dim]")


@cli.command()
def report():
    """Fetch latest data and send an email report now."""
    db.init_db()
    config = cfg_mod.load_config()
    if not config["email"].get("enabled"):
        console.print("[yellow]Email not configured. Run 'python main.py setup' first.[/yellow]")
        return

    console.print("Fetching data...")
    refresh_all(config)

    stocks = db.get_all_stocks()
    earnings = db.get_upcoming_earnings()
    alerts = db.get_recent_alerts(20)
    html = alert_mod.build_email_report(stocks, earnings, alerts)
    ok = alert_mod.send_email("Stock Tracker — Manual Report", html, config)
    if ok:
        console.print(f"[green]Report sent to {config['email']['recipient']}![/green]")
    else:
        console.print("[red]Failed to send email. Check your setup.[/red]")


@cli.command()
def schedule():
    """Run background monitoring — checks alerts every 5 min, daily email at close."""
    db.init_db()
    config = cfg_mod.load_config()
    console.print("[bold blue]Background scheduler started.[/bold blue] Press Ctrl+C to stop.\n")
    console.print("  • Alert checks every 5 minutes during market hours")
    console.print("  • Daily email report at market close (4 PM ET)\n")

    try:
        from zoneinfo import ZoneInfo
        et = ZoneInfo("America/New_York")
    except Exception:
        et = None

    last_refresh = 0
    daily_report_sent = False

    while True:
        now = datetime.now(et) if et else datetime.now()
        market_open = _is_market_open()

        # Reset daily flag
        if not market_open and now.hour < 9:
            daily_report_sent = False

        if market_open and (time.time() - last_refresh) >= 300:
            console.print(f"[dim]{datetime.now().strftime('%H:%M:%S')} Refreshing...[/dim]")
            refresh_all(config)
            last_refresh = time.time()

        # Daily close report
        if et and hasattr(now, "hour") and now.hour == 16 and now.minute < 10 and not daily_report_sent:
            if config["email"].get("enabled"):
                stocks = db.get_all_stocks()
                earnings = db.get_upcoming_earnings()
                alerts = db.get_recent_alerts(20)
                html = alert_mod.build_email_report(stocks, earnings, alerts)
                ok = alert_mod.send_email("Stock Tracker — Daily Close Report", html, config)
                if ok:
                    console.print(f"[green]{datetime.now().strftime('%H:%M')} Daily report sent.[/green]")
                daily_report_sent = True

        time.sleep(30)


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind to")
@click.option("--port", default=5443, show_default=True, help="HTTPS port")
@click.option("--http-port", default=5080, show_default=True, help="HTTP redirect port (0 to disable)")
@click.option("--no-tls", is_flag=True, default=False, help="Run plain HTTP (for ngrok / reverse proxy / cloud)")
def serve(host, port, http_port, no_tls):
    """Start the subscriber signup web server (HTTPS with auto-generated TLS cert)."""
    import os as _os
    import socket as _socket
    from tracker.web import create_app

    db.init_db()
    config = cfg_mod.load_config()
    app = create_app()

    # ── background data refresh (runs on Railway and all serve modes) ─────────
    def _bg_refresh_loop():
        try:
            refresh_all(config)
        except Exception as _e:
            print(f"[refresh] STARTUP ERROR: {_e}", flush=True)
            import traceback; traceback.print_exc()
        interval = config.get("refresh_interval", 300)
        while True:
            time.sleep(interval)
            try:
                refresh_all(config)
            except Exception:
                pass

    threading.Thread(target=_bg_refresh_loop, daemon=True).start()

    # ── plain HTTP mode (for ngrok / reverse proxy / cloud) ──────────────────
    if no_tls:
        # Railway (and most PaaS) set $PORT; fall back to --http-port or 5080
        http_only_port = int(_os.environ.get("PORT", http_port if http_port else 5080))
        try:
            lan_ip = _socket.gethostbyname(_socket.gethostname())
        except Exception:
            lan_ip = "your-ip"
        console.print(f"[bold green]HTTP server running[/bold green] (plain, for use behind ngrok/proxy)")
        console.print(f"  Local:   http://localhost:{http_only_port}")
        console.print(f"  Network: http://{lan_ip}:{http_only_port}")
        console.print("\n[dim]Press Ctrl+C to stop.[/dim]\n")
        import logging
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        app.run(host=host, port=http_only_port, debug=False, threaded=True)
        return

    import ssl as _ssl
    from tracker.ssl_cert import ensure_cert

    # ── generate / reuse TLS cert ─────────────────────────────────────────────
    console.print("[bold blue]Preparing TLS certificate...[/bold blue]")
    cert_path, key_path = ensure_cert()
    console.print(f"  Certificate: [dim]{cert_path}[/dim]")

    ssl_ctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.minimum_version = _ssl.TLSVersion.TLSv1_2
    ssl_ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))

    # ── HTTP -> HTTPS redirect server (background thread) ────────────────────
    if http_port:
        from flask import Flask as _Flask, request as _req, redirect as _redir_fn
        redirect_app = _Flask("redirect")
        _https_port = port

        @redirect_app.route("/", defaults={"path": ""})
        @redirect_app.route("/<path:path>")
        def _redir(path):
            host_only = _req.host.split(":")[0]
            target = f"https://{host_only}:{_https_port}/{path}"
            if _req.query_string:
                target += "?" + _req.query_string.decode()
            return _redir_fn(target, code=301)

        def _run_redirect():
            import logging
            log = logging.getLogger("werkzeug")
            log.setLevel(logging.ERROR)
            redirect_app.run(host=host, port=http_port, debug=False)

        threading.Thread(target=_run_redirect, daemon=True).start()

    # ── resolve LAN IP for display ────────────────────────────────────────────
    try:
        lan_ip = _socket.gethostbyname(_socket.gethostname())
    except Exception:
        lan_ip = "your-ip"

    https_local = f"https://localhost:{port}"
    https_lan = f"https://{lan_ip}:{port}"

    console.print(f"\n[bold green]HTTPS server running[/bold green]")
    console.print(f"  Local:   {https_local}")
    console.print(f"  Network: {https_lan}")
    if http_port:
        console.print(f"  HTTP redirect: port {http_port} -> {port}")
    console.print()
    console.print("[yellow]First-time browser warning:[/yellow] your browser will show a security")
    console.print("warning because the cert is self-signed. Click 'Advanced' then 'Proceed'.")
    console.print("[dim]To avoid the warning, install certs/server.crt as a trusted CA on each device.[/dim]")
    console.print("\n[dim]Press Ctrl+C to stop.[/dim]\n")

    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.WARNING)
    app.run(host=host, port=port, ssl_context=ssl_ctx, debug=False, threaded=True)


@cli.command(name="subscribers")
def list_subscribers():
    """List all active subscribers."""
    db.init_db()
    subs = db.get_active_subscribers()
    if not subs:
        console.print("[dim]No active subscribers.[/dim]")
        return

    from rich.table import Table
    table = Table(title=f"Active Subscribers ({len(subs)})", border_style="blue",
                  header_style="bold white on dark_blue")
    table.add_column("Email", style="bold")
    table.add_column("Stocks")
    table.add_column("Phone")
    table.add_column("Carrier")
    table.add_column("Subscribed")
    for s in subs:
        stocks  = ", ".join(s["stocks"]) if s["stocks"] else "[dim]all[/dim]"
        created = (s.get("created_at") or "")[:10]
        phone   = s.get("phone_number") or "[dim]-[/dim]"
        carrier = s.get("carrier") or "[dim]-[/dim]"
        table.add_row(s["email"], stocks, phone, carrier, created)
    console.print(table)


# ── knowledge base ────────────────────────────────────────────────────────────

def _render_topic(key: str) -> bool:
    """Render a knowledge base topic to the console. Returns False if not found."""
    from rich.rule import Rule
    from rich.markdown import Markdown

    topic = kb_mod.get_topic(key)
    if not topic:
        # fuzzy: search for it
        results = kb_mod.search(key)
        if results:
            console.print(f"[yellow]Topic '{key}' not found. Did you mean:[/yellow]")
            for k, title in results[:5]:
                console.print(f"  [cyan]{k}[/cyan] — {title}")
        else:
            console.print(f"[red]No topic found for '{key}'. Run 'python main.py learn' to see all topics.[/red]")
        return False

    cat_color = {
        "Indicators": "bright_cyan", "Patterns": "bright_yellow",
        "Sectors": "bright_magenta", "Concepts": "bright_white",
        "Risk Management": "bright_red",
    }.get(topic["category"], "white")

    console.print()
    console.print(Rule(f"[bold]{topic['title']}[/bold]", style=cat_color))
    console.print(f"[{cat_color}]Category:[/{cat_color}] {topic['category']}\n")
    console.print(f"[bold]Overview[/bold]")
    console.print(f"  {topic['summary']}\n")

    for section in topic["sections"]:
        console.print(f"[bold underline]{section['heading']}[/bold underline]")
        for line in section["content"].split("\n"):
            console.print(f"  {line}")
        console.print()

    if topic.get("quick_tips"):
        console.print("[bold]Quick Tips[/bold]")
        for tip in topic["quick_tips"]:
            console.print(f"  [green]+[/green] {tip}")
        console.print()

    if topic.get("related"):
        rel = ", ".join(f"[cyan]{r}[/cyan]" for r in topic["related"])
        console.print(f"[dim]Related topics:[/dim] {rel}")
    console.print()
    return True


@cli.command()
@click.argument("topic", required=False, default="")
@click.option("--list", "list_all", is_flag=True, help="List all topics")
@click.option("--search", "query", default="", help="Search topics")
def learn(topic, list_all, query):
    """Browse the trading knowledge base. Run with no args for the index."""
    from rich.columns import Columns
    from rich.panel import Panel as RPanel

    if query:
        results = kb_mod.search(query)
        if results:
            console.print(f"\n[bold]Search results for '{query}':[/bold]\n")
            for k, title in results:
                console.print(f"  [cyan]{k:30s}[/cyan]  {title}")
        else:
            console.print(f"[yellow]No results for '{query}'.[/yellow]")
        return

    if topic:
        _render_topic(topic)
        return

    # index view
    by_cat = kb_mod.list_by_category()
    cat_colors = {
        "Indicators":      "bright_cyan",
        "Patterns":        "bright_yellow",
        "Sectors":         "bright_magenta",
        "Concepts":        "bright_white",
        "Risk Management": "bright_red",
    }

    console.print()
    console.print("[bold blue]  Trading Knowledge Base[/bold blue]")
    console.print("[dim]  Run: python main.py learn <topic-key>   e.g. python main.py learn rsi[/dim]\n")

    panels = []
    for cat in kb_mod.CATEGORIES:
        entries = by_cat.get(cat, [])
        color = cat_colors.get(cat, "white")
        lines = "\n".join(f"  [cyan]{k}[/cyan]" for k, _ in entries)
        panels.append(RPanel(lines, title=f"[bold {color}]{cat}[/bold {color}]", border_style=color, expand=True))

    console.print(Columns(panels, equal=True))
    console.print("\n[dim]  Use --search <query> to search, or --list to see all topic keys.[/dim]\n")


# ── sector management ─────────────────────────────────────────────────────────

@cli.group()
def sector():
    """Manage stock sector assignments."""
    pass


@sector.command(name="list")
def sector_list():
    """List all sectors and their assigned stocks."""
    config = cfg_mod.load_config()
    stock_sectors = config.get("stock_sectors", {})

    for sect_name, info in sec_mod.SECTOR_CATALOG.items():
        color = sec_mod.get_sector_color(sect_name)
        # stocks from catalog + any manually assigned
        assigned = [s for s, sec in stock_sectors.items() if sec == sect_name]
        catalog_syms = list(info["stocks"].keys())
        all_syms = sorted(set(catalog_syms + assigned))
        in_watchlist = set(config["watchlist"])

        console.print(f"\n[bold {color}]{sect_name}[/bold {color}]")
        console.print(f"  [dim]{info['description']}[/dim]")
        for sym in all_syms:
            tag = "[green] (watching)[/green]" if sym in in_watchlist else "[dim] (not tracking)[/dim]"
            desc = info["stocks"].get(sym, "")
            console.print(f"    {sym:6s}{tag}  [dim]{desc}[/dim]")


@sector.command(name="load")
@click.argument("sector_name")
@click.option("--all", "load_all", is_flag=True, help="Load all stocks from this sector")
def sector_load(sector_name, load_all):
    """Add all stocks from a sector to your watchlist.

    SECTOR_NAME can be a partial match (e.g. 'ai', 'quantum', 'etf').
    """
    config = cfg_mod.load_config()
    # fuzzy match
    matched = None
    name_lower = sector_name.lower()
    for k in sec_mod.SECTOR_CATALOG:
        if name_lower in k.lower():
            matched = k
            break
    if not matched:
        console.print(f"[red]No sector matching '{sector_name}'. Run 'python main.py sector list' to see sectors.[/red]")
        return

    info = sec_mod.SECTOR_CATALOG[matched]
    syms = list(info["stocks"].keys())
    watchlist = config["watchlist"]
    stock_sectors = config.get("stock_sectors", {})
    added = []
    for sym in syms:
        if sym not in watchlist:
            watchlist.append(sym)
            added.append(sym)
        stock_sectors[sym] = matched

    config["watchlist"] = watchlist
    config["stock_sectors"] = stock_sectors
    cfg_mod.save_config(config)

    color = sec_mod.get_sector_color(matched)
    console.print(f"\n[bold {color}]{matched}[/bold {color}]")
    if added:
        console.print(f"  [green]Added to watchlist:[/green] {', '.join(added)}")
    console.print(f"  [dim]Already tracking:[/dim] {', '.join(s for s in syms if s not in added)}")


@sector.command(name="assign")
@click.argument("symbol")
@click.argument("sector_name")
def sector_assign(symbol, sector_name):
    """Assign a stock to a specific sector.

    Example: python main.py sector assign IONQ 'Quantum Computing'
    """
    config = cfg_mod.load_config()
    matched = None
    for k in sec_mod.SECTOR_CATALOG:
        if sector_name.lower() in k.lower():
            matched = k
            break
    if not matched:
        matched = sector_name  # allow custom sector names

    stock_sectors = config.get("stock_sectors", {})
    stock_sectors[symbol.upper()] = matched
    config["stock_sectors"] = stock_sectors
    cfg_mod.save_config(config)
    console.print(f"[green]{symbol.upper()}[/green] assigned to [bold]{matched}[/bold]")


# ── social media ─────────────────────────────────────────────────────────────

@cli.group()
def social():
    """Social media posting commands."""
    pass


@social.command(name="preview")
def social_preview():
    """Preview the market-update post that would be sent to Twitter."""
    db.init_db()
    config = cfg_mod.load_config()
    stocks = db.get_all_stocks()
    if not stocks:
        console.print("[yellow]No stock data yet. Run the dashboard first to populate data.[/yellow]")
        return
    public_url = config.get("social", {}).get("public_url", "")
    text = social_mod.generate_market_post(stocks, public_url)
    console.print(f"\n[bold]Market update post ({len(text)}/280 chars):[/bold]\n")
    console.print(text)
    console.print()


@social.command(name="post")
def social_post():
    """Post a market update to Twitter/X now."""
    db.init_db()
    config = cfg_mod.load_config()
    stocks = db.get_all_stocks()
    if not stocks:
        console.print("[yellow]No stock data yet. Run the dashboard first.[/yellow]")
        return
    ok = social_mod.post_market_update(stocks, config)
    if ok:
        console.print("[green]Market update posted to Twitter![/green]")
    else:
        console.print("[red]Failed to post. Check Twitter credentials in 'python main.py setup'.[/red]")


@social.command(name="cta")
def social_cta():
    """Post a subscribe call-to-action tweet."""
    db.init_db()
    config = cfg_mod.load_config()
    public_url = config.get("social", {}).get("public_url", "")
    if not public_url:
        console.print("[red]Set your public URL first: run 'python main.py setup'.[/red]")
        return
    watchlist = config.get("watchlist", [])
    text = social_mod.generate_subscribe_post(public_url, watchlist)
    console.print(f"\n[bold]CTA post preview ({len(text)}/280 chars):[/bold]\n")
    console.print(text)
    console.print()
    ok = social_mod.post_to_twitter(text, config)
    if ok:
        console.print("[green]CTA posted to Twitter![/green]")
    else:
        console.print("[yellow]Twitter not configured -- post text printed above for manual sharing.[/yellow]")


@social.command(name="schedule-posts")
@click.option("--interval", default=4, show_default=True, help="Hours between market-update posts")
def social_schedule(interval):
    """Continuously post market updates to Twitter at a set interval."""
    db.init_db()
    config = cfg_mod.load_config()
    console.print(f"[bold blue]Social scheduler started[/bold blue] -- posting every {interval}h. Ctrl+C to stop.\n")
    while True:
        stocks = db.get_all_stocks()
        if stocks:
            ok = social_mod.post_market_update(stocks, config)
            status = "[green]posted[/green]" if ok else "[yellow]skipped (no credentials)[/yellow]"
            console.print(f"[dim]{datetime.now().strftime('%H:%M')}[/dim] Twitter post {status}")
        time.sleep(interval * 3600)


if __name__ == "__main__":
    cli()
