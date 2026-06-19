import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

# Use persistent volume on Railway (/app/data), fall back to repo root locally
_DATA_DIR = Path(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "")) or Path(__file__).parent.parent
if os.environ.get("RAILWAY_VOLUME_MOUNT_PATH"):
    _DATA_DIR = Path(os.environ["RAILWAY_VOLUME_MOUNT_PATH"])
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
else:
    _DATA_DIR = Path(__file__).parent.parent

DB_PATH = _DATA_DIR / "stocks.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS stocks (
                symbol TEXT PRIMARY KEY,
                price REAL,
                prev_close REAL,
                change_pct REAL,
                volume INTEGER,
                avg_volume INTEGER,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                bb_pband REAL,
                ma20 REAL,
                ma50 REAL,
                ma200 REAL,
                prediction TEXT,
                prediction_confidence REAL,
                rule_signals TEXT,
                sector TEXT DEFAULT 'General',
                last_updated TEXT
            );

            CREATE TABLE IF NOT EXISTS earnings (
                symbol TEXT,
                earnings_date TEXT,
                eps_estimate REAL,
                actual_eps REAL,
                surprise_pct REAL,
                avg_reaction_pct REAL,
                days_until INTEGER,
                is_upcoming INTEGER DEFAULT 0,
                PRIMARY KEY (symbol, earnings_date)
            );

            CREATE TABLE IF NOT EXISTS alerts_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT,
                symbol TEXT,
                message TEXT,
                severity TEXT,
                created_at TEXT,
                email_sent INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                stocks TEXT NOT NULL DEFAULT '[]',
                token TEXT UNIQUE NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                phone_number TEXT DEFAULT '',
                carrier TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS predictions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                prediction_date TEXT NOT NULL,
                signal TEXT NOT NULL,
                confidence REAL,
                combined_prob REAL,
                price_at_prediction REAL,
                price_scored REAL,
                actual_return_pct REAL,
                was_correct INTEGER,
                scored_at TEXT
            );

            CREATE TABLE IF NOT EXISTS options_recs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                opt_type TEXT NOT NULL,
                strike REAL,
                expiry TEXT,
                days_out INTEGER,
                bid REAL,
                ask REAL,
                last_price REAL,
                iv REAL,
                open_interest INTEGER,
                volume INTEGER,
                score REAL,
                confidence REAL,
                reason TEXT,
                current_price REAL,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS sweeps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sweep_type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT,
                opt_type TEXT,
                strike REAL,
                expiry TEXT,
                days_out INTEGER,
                opt_volume INTEGER,
                open_interest INTEGER,
                vol_oi_ratio REAL,
                last_price REAL,
                iv_pct REAL,
                total_premium REAL,
                otm_pct REAL,
                aggression REAL,
                current_price REAL,
                notional REAL,
                vol_ratio REAL,
                change_pct REAL,
                is_golden INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS subscriber_orders (
                order_id TEXT PRIMARY KEY,
                subscriber_email TEXT NOT NULL,
                symbol TEXT NOT NULL DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS managed_option_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_email TEXT NOT NULL,
                order_id TEXT NOT NULL DEFAULT '',
                underlying TEXT NOT NULL,
                occ_symbol TEXT NOT NULL,
                expiry TEXT NOT NULL,
                strike REAL NOT NULL,
                opt_type TEXT NOT NULL,
                qty INTEGER NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss_pct REAL NOT NULL DEFAULT 20,
                trail_trigger_pct REAL NOT NULL DEFAULT 20,
                trail_pct REAL NOT NULL DEFAULT 5,
                status TEXT NOT NULL DEFAULT 'active',
                trailing_active INTEGER NOT NULL DEFAULT 0,
                peak_price REAL,
                trail_stop_price REAL,
                close_order_id TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
        """)
    _migrate_columns()


def _migrate_columns() -> None:
    """Add columns that may be missing from older database versions."""
    with get_connection() as conn:
        # stocks table
        stock_cols = [r[1] for r in conn.execute("PRAGMA table_info(stocks)").fetchall()]
        if stock_cols and "sector" not in stock_cols:
            conn.execute("ALTER TABLE stocks ADD COLUMN sector TEXT DEFAULT 'General'")
        if stock_cols and "fib_signal" not in stock_cols:
            conn.execute("ALTER TABLE stocks ADD COLUMN fib_signal INTEGER DEFAULT 0")
        if stock_cols and "fib_level" not in stock_cols:
            conn.execute("ALTER TABLE stocks ADD COLUMN fib_level TEXT DEFAULT ''")
        if stock_cols and "uptrend_prob" not in stock_cols:
            conn.execute("ALTER TABLE stocks ADD COLUMN uptrend_prob REAL")
        if stock_cols and "demand_zone" not in stock_cols:
            conn.execute("ALTER TABLE stocks ADD COLUMN demand_zone REAL")
        if stock_cols and "supply_zone" not in stock_cols:
            conn.execute("ALTER TABLE stocks ADD COLUMN supply_zone REAL")
        if stock_cols and "poc_price" not in stock_cols:
            conn.execute("ALTER TABLE stocks ADD COLUMN poc_price REAL")
        # subscribers table
        try:
            sub_cols = [r[1] for r in conn.execute("PRAGMA table_info(subscribers)").fetchall()]
            if sub_cols:
                if "phone_number" not in sub_cols:
                    conn.execute("ALTER TABLE subscribers ADD COLUMN phone_number TEXT DEFAULT ''")
                if "carrier" not in sub_cols:
                    conn.execute("ALTER TABLE subscribers ADD COLUMN carrier TEXT DEFAULT ''")
        except Exception:
            pass
        # Fix sector/last_updated swap: if any sector value looks like a
        # datetime (starts with "20"), swap them back.
        try:
            bad = conn.execute(
                "SELECT COUNT(*) FROM stocks WHERE sector LIKE '20%'"
            ).fetchone()[0]
            if bad > 0:
                conn.execute("""
                    UPDATE stocks
                    SET sector = last_updated,
                        last_updated = sector
                    WHERE sector LIKE '20%'
                """)
        except Exception:
            pass

        # login_otps table
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_otps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    code TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    used INTEGER DEFAULT 0
                )
            """)
        except Exception:
            pass

        # predictions_log table -- create if missing (legacy DBs pre-v2)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    prediction_date TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL,
                    combined_prob REAL,
                    price_at_prediction REAL,
                    price_scored REAL,
                    actual_return_pct REAL,
                    was_correct INTEGER,
                    scored_at TEXT
                )
            """)
        except Exception:
            pass


def upsert_stock(data: dict) -> None:
    data["rule_signals"] = json.dumps(data.get("rule_signals", []))
    data.setdefault("sector", "General")
    data["last_updated"] = datetime.now().isoformat()
    data.setdefault("demand_zone", None)
    data.setdefault("supply_zone", None)
    data.setdefault("poc_price",   None)
    with get_connection() as conn:
        # Use explicit column names so physical column order (which can vary
        # between fresh creates and ALTER TABLE migrations) never matters.
        conn.execute("""
            INSERT INTO stocks
                (symbol, price, prev_close, change_pct, volume, avg_volume,
                 rsi, macd, macd_signal, bb_pband, ma20, ma50, ma200,
                 prediction, prediction_confidence, rule_signals, sector,
                 fib_signal, fib_level, uptrend_prob,
                 demand_zone, supply_zone, poc_price, last_updated)
            VALUES
                (:symbol, :price, :prev_close, :change_pct, :volume, :avg_volume,
                 :rsi, :macd, :macd_signal, :bb_pband, :ma20, :ma50, :ma200,
                 :prediction, :prediction_confidence, :rule_signals, :sector,
                 :fib_signal, :fib_level, :uptrend_prob,
                 :demand_zone, :supply_zone, :poc_price, :last_updated)
            ON CONFLICT(symbol) DO UPDATE SET
                price=excluded.price, prev_close=excluded.prev_close,
                change_pct=excluded.change_pct, volume=excluded.volume,
                avg_volume=excluded.avg_volume, rsi=excluded.rsi,
                macd=excluded.macd, macd_signal=excluded.macd_signal,
                bb_pband=excluded.bb_pband, ma20=excluded.ma20,
                ma50=excluded.ma50, ma200=excluded.ma200,
                prediction=excluded.prediction,
                prediction_confidence=excluded.prediction_confidence,
                rule_signals=excluded.rule_signals,
                sector=excluded.sector,
                fib_signal=excluded.fib_signal,
                fib_level=excluded.fib_level,
                uptrend_prob=excluded.uptrend_prob,
                demand_zone=excluded.demand_zone,
                supply_zone=excluded.supply_zone,
                poc_price=excluded.poc_price,
                last_updated=excluded.last_updated
        """, data)


def get_all_stocks() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM stocks ORDER BY symbol").fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["rule_signals"] = json.loads(d.get("rule_signals") or "[]")
        result.append(d)
    return result


def upsert_earnings(data: dict) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO earnings VALUES (
                :symbol, :earnings_date, :eps_estimate, :actual_eps,
                :surprise_pct, :avg_reaction_pct, :days_until, :is_upcoming
            )
            ON CONFLICT(symbol, earnings_date) DO UPDATE SET
                eps_estimate=excluded.eps_estimate,
                days_until=excluded.days_until,
                avg_reaction_pct=excluded.avg_reaction_pct,
                is_upcoming=excluded.is_upcoming
        """, data)


def get_upcoming_earnings() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM earnings WHERE is_upcoming=1
            ORDER BY days_until ASC
        """).fetchall()
    return [dict(r) for r in rows]


def log_alert(alert_type: str, symbol: str, message: str, severity: str, email_sent: bool = False) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO alerts_log (alert_type, symbol, message, severity, created_at, email_sent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (alert_type, symbol, message, severity, datetime.now().isoformat(), int(email_sent)))


def get_recent_alerts(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM alerts_log ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def was_alert_sent_today(alert_type: str, symbol: str) -> bool:
    today = datetime.now().date().isoformat()
    with get_connection() as conn:
        row = conn.execute("""
            SELECT id FROM alerts_log
            WHERE alert_type=? AND symbol=? AND created_at LIKE ?
        """, (alert_type, symbol, f"{today}%")).fetchone()
    return row is not None


def was_alert_sent_recently(alert_type: str, symbol: str, days: int = 7) -> bool:
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM alerts_log WHERE alert_type=? AND symbol=? AND created_at>=?",
            (alert_type, symbol, cutoff)
        ).fetchone()
    return row is not None


# ── subscribers ───────────────────────────────────────────────────────────────

def add_subscriber(email: str, stocks: list[str], phone_number: str = "", carrier: str = "") -> str:
    import secrets
    token = secrets.token_urlsafe(24)
    with get_connection() as conn:
        try:
            conn.execute("""
                INSERT INTO subscribers (email, stocks, token, active, phone_number, carrier, created_at)
                VALUES (?, ?, ?, 1, ?, ?, ?)
            """, (email.lower().strip(), json.dumps(stocks), token,
                  phone_number.strip(), carrier.strip(), datetime.now().isoformat()))
            return token
        except sqlite3.IntegrityError:
            conn.execute("""
                UPDATE subscribers SET active=1, stocks=?, phone_number=?, carrier=?, created_at=?
                WHERE email=?
            """, (json.dumps(stocks), phone_number.strip(), carrier.strip(),
                  datetime.now().isoformat(), email.lower().strip()))
            row = conn.execute("SELECT token FROM subscribers WHERE email=?",
                               (email.lower().strip(),)).fetchone()
            return row["token"] if row else token


def remove_subscriber(token: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("UPDATE subscribers SET active=0 WHERE token=?", (token,))
        return cur.rowcount > 0


def get_active_subscribers() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM subscribers WHERE active=1 ORDER BY created_at
        """).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["stocks"] = json.loads(d.get("stocks") or "[]")
        result.append(d)
    return result


def get_subscriber_by_token(token: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM subscribers WHERE token=?", (token,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["stocks"] = json.loads(d.get("stocks") or "[]")
    return d


# ── Prediction accuracy tracking ──────────────────────────────────────────────

def log_prediction(symbol: str, signal: str, confidence: float,
                   combined_prob: float, price: float) -> None:
    """Record a prediction so it can be scored against actual outcome later."""
    today = datetime.now().date().isoformat()
    with get_connection() as conn:
        # Only log once per symbol per day (avoid duplicate refresh entries)
        existing = conn.execute(
            "SELECT id FROM predictions_log WHERE symbol=? AND prediction_date=?",
            (symbol, today)
        ).fetchone()
        if existing:
            # Update in case signal changed
            conn.execute("""
                UPDATE predictions_log
                SET signal=?, confidence=?, combined_prob=?, price_at_prediction=?
                WHERE symbol=? AND prediction_date=?
            """, (signal, confidence, combined_prob, price, symbol, today))
        else:
            conn.execute("""
                INSERT INTO predictions_log
                    (symbol, prediction_date, signal, confidence, combined_prob,
                     price_at_prediction)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (symbol, today, signal, confidence, combined_prob, price))


def score_pending_predictions(current_prices: dict[str, float],
                               score_after_days: int = 5) -> int:
    """
    Score predictions that were made >= score_after_days ago.
    Correct: BULLISH and price up; BEARISH and price down; NEUTRAL not scored.
    Returns number of predictions newly scored.
    """
    from datetime import timedelta
    cutoff = (datetime.now().date() - timedelta(days=score_after_days)).isoformat()
    scored_count = 0
    with get_connection() as conn:
        pending = conn.execute("""
            SELECT id, symbol, signal, price_at_prediction
            FROM predictions_log
            WHERE was_correct IS NULL
              AND prediction_date <= ?
              AND signal != 'NEUTRAL'
        """, (cutoff,)).fetchall()

        for row in pending:
            sym = row["symbol"]
            if sym not in current_prices:
                continue
            curr_price   = current_prices[sym]
            entry_price  = row["price_at_prediction"]
            if not entry_price or entry_price == 0:
                continue

            ret_pct = (curr_price - entry_price) / entry_price * 100
            signal  = row["signal"]
            if signal == "BULLISH":
                correct = 1 if ret_pct > 0 else 0
            elif signal == "BEARISH":
                correct = 1 if ret_pct < 0 else 0
            else:
                continue

            conn.execute("""
                UPDATE predictions_log
                SET price_scored=?, actual_return_pct=?, was_correct=?, scored_at=?
                WHERE id=?
            """, (curr_price, round(ret_pct, 3), correct,
                  datetime.now().isoformat(), row["id"]))
            scored_count += 1
    return scored_count


def get_prediction_accuracy(min_scored: int = 5) -> dict:
    """
    Return accuracy statistics for scored predictions.
    Only counts BULLISH and BEARISH (NEUTRAL excluded).
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT signal, was_correct, actual_return_pct, confidence
            FROM predictions_log
            WHERE was_correct IS NOT NULL
        """).fetchall()

    if len(rows) < min_scored:
        return {"total": len(rows), "insufficient_data": True}

    total      = len(rows)
    correct    = sum(1 for r in rows if r["was_correct"] == 1)
    bull_rows  = [r for r in rows if r["signal"] == "BULLISH"]
    bear_rows  = [r for r in rows if r["signal"] == "BEARISH"]

    bull_acc = (sum(1 for r in bull_rows if r["was_correct"]) / len(bull_rows) * 100
                if bull_rows else None)
    bear_acc = (sum(1 for r in bear_rows if r["was_correct"]) / len(bear_rows) * 100
                if bear_rows else None)

    # High-confidence subset (confidence >= 0.5)
    hi_conf = [r for r in rows if (r["confidence"] or 0) >= 0.5]
    hi_acc  = (sum(1 for r in hi_conf if r["was_correct"]) / len(hi_conf) * 100
               if hi_conf else None)

    avg_ret = sum(r["actual_return_pct"] or 0 for r in rows) / total

    return {
        "total":            total,
        "correct":          correct,
        "accuracy_pct":     round(correct / total * 100, 1),
        "bull_total":       len(bull_rows),
        "bull_accuracy_pct":round(bull_acc, 1) if bull_acc is not None else None,
        "bear_total":       len(bear_rows),
        "bear_accuracy_pct":round(bear_acc, 1) if bear_acc is not None else None,
        "hi_conf_total":    len(hi_conf),
        "hi_conf_acc_pct":  round(hi_acc, 1) if hi_acc is not None else None,
        "avg_return_pct":   round(avg_ret, 2),
        "insufficient_data":False,
    }


def get_recent_predictions(limit: int = 20) -> list[dict]:
    """Return most recent prediction log entries (newest first)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM predictions_log
            ORDER BY prediction_date DESC, id DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


# ── Options recommendations ───────────────────────────────────────────────────

def clear_option_recs() -> None:
    """Delete all existing options recommendations (called before each refresh)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM options_recs")


def upsert_option_recs(recs: list[dict]) -> None:
    """Insert a batch of option recommendations."""
    if not recs:
        return
    now = datetime.now().isoformat()
    with get_connection() as conn:
        for r in recs:
            conn.execute("""
                INSERT INTO options_recs
                    (symbol, opt_type, strike, expiry, days_out, bid, ask,
                     last_price, iv, open_interest, volume, score, confidence,
                     reason, current_price, created_at)
                VALUES
                    (:symbol, :type, :strike, :expiry, :days_out, :bid, :ask,
                     :last, :iv, :open_interest, :volume, :score, :confidence,
                     :reason, :current_price, :created_at)
            """, {**r, "created_at": now})


def get_option_recs(limit: int = 40) -> list[dict]:
    """Return the most recent options recommendations, sorted by score desc."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM options_recs
            ORDER BY score DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


# ── Sweeps / Dark Pool ────────────────────────────────────────────────────────

def upsert_sweeps(sweeps: list[dict]) -> None:
    """Replace today's sweeps with the latest scan results."""
    if not sweeps:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        conn.execute("DELETE FROM sweeps WHERE created_at LIKE ?", (f"{today}%",))
        for s in sweeps:
            conn.execute("""
                INSERT INTO sweeps (
                    sweep_type, symbol, direction, opt_type, strike, expiry,
                    days_out, opt_volume, open_interest, vol_oi_ratio, last_price,
                    iv_pct, total_premium, otm_pct, aggression, current_price,
                    notional, vol_ratio, change_pct, is_golden, created_at
                ) VALUES (
                    :sweep_type, :symbol, :direction, :opt_type, :strike, :expiry,
                    :days_out, :opt_volume, :open_interest, :vol_oi_ratio, :last_price,
                    :iv_pct, :total_premium, :otm_pct, :aggression, :current_price,
                    :notional, :vol_ratio, :change_pct, :is_golden, :created_at
                )
            """, s)


def get_sweeps(sweep_type: str = "", limit: int = 30) -> list[dict]:
    """Return recent sweeps, optionally filtered by type."""
    with get_connection() as conn:
        if sweep_type:
            rows = conn.execute("""
                SELECT * FROM sweeps WHERE sweep_type = ?
                ORDER BY total_premium DESC, notional DESC, created_at DESC
                LIMIT ?
            """, (sweep_type, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM sweeps
                ORDER BY total_premium DESC, notional DESC, created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_all_sweeps_today() -> dict:
    """Return golden, options sweeps, and dark pool blocks from today."""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sweeps WHERE created_at LIKE ? ORDER BY total_premium DESC, notional DESC",
            (f"{today}%",)
        ).fetchall()
    all_rows = [dict(r) for r in rows]
    return {
        "golden":    [r for r in all_rows if r["sweep_type"] == "GOLDEN_SWEEP"],
        "calls":     [r for r in all_rows if r["sweep_type"] == "CALL_SWEEP"],
        "puts":      [r for r in all_rows if r["sweep_type"] == "PUT_SWEEP"],
        "dark_pool": [r for r in all_rows if r["sweep_type"] == "DARK_POOL"],
    }


# ── Key-value store ───────────────────────────────────────────────────────────

def set_kv(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO kv_store(key, value, updated_at) VALUES(?,?,?)",
            (key, value, datetime.now().isoformat())
        )


def get_kv(key: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM kv_store WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None


# ── Auth / login OTPs ─────────────────────────────────────────────────────────

def is_active_subscriber_email(email: str) -> bool:
    """True if email belongs to an active subscriber (excludes SMS-only placeholders)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM subscribers WHERE email=? AND active=1 AND email NOT LIKE 'sms+%'",
            (email.lower().strip(),)
        ).fetchone()
    return row is not None


def create_login_otp(email: str) -> str:
    """Generate a 6-digit OTP, store it (15 min TTL), return the code."""
    import random as _r, time as _t
    code = f"{_r.randint(0, 999999):06d}"
    ts = _t.time()
    with get_connection() as conn:
        # Remove stale OTPs for this email and any globally expired ones
        conn.execute("DELETE FROM login_otps WHERE email=? OR created_at<?",
                     (email.lower().strip(), ts - 900))
        conn.execute("INSERT INTO login_otps (email, code, created_at) VALUES (?,?,?)",
                     (email.lower().strip(), code, ts))
    return code


def verify_login_otp(email: str, code: str) -> bool:
    """Verify OTP — returns True once, marks it used."""
    import time as _t
    ts = _t.time()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM login_otps WHERE email=? AND code=? AND used=0 AND created_at>?",
            (email.lower().strip(), code.strip(), ts - 900)
        ).fetchone()
        if row:
            conn.execute("UPDATE login_otps SET used=1 WHERE id=?", (row["id"],))
            return True
    return False


# ── Per-subscriber order ownership ────────────────────────────────────────────

def record_subscriber_order(order_id: str, subscriber_email: str, symbol: str) -> None:
    """Record that subscriber_email placed order_id for symbol."""
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscriber_orders (order_id, subscriber_email, symbol) VALUES (?,?,?)",
            (order_id, subscriber_email, symbol),
        )


def get_subscriber_order_ids(subscriber_email: str) -> list:
    """Return all Alpaca order IDs placed by this subscriber."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT order_id FROM subscriber_orders WHERE subscriber_email=?",
            (subscriber_email,),
        ).fetchall()
    return [r["order_id"] for r in rows]


def get_subscriber_symbols(subscriber_email: str) -> list:
    """Return distinct root symbols this subscriber has traded (for position filtering)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT symbol FROM subscriber_orders WHERE subscriber_email=?",
            (subscriber_email,),
        ).fetchall()
    return [r["symbol"] for r in rows]


def is_subscriber_order(order_id: str, subscriber_email: str) -> bool:
    """Return True if this order belongs to subscriber_email."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM subscriber_orders WHERE order_id=? AND subscriber_email=?",
            (order_id, subscriber_email),
        ).fetchone()
    return row is not None


# ── Managed option positions ───────────────────────────────────────────────────

def create_managed_option(
    subscriber_email: str, order_id: str, underlying: str, occ_symbol: str,
    expiry: str, strike: float, opt_type: str, qty: int, entry_price: float,
    stop_loss_pct: float = 20.0, trail_trigger_pct: float = 20.0, trail_pct: float = 5.0,
) -> int:
    """Insert a new managed option position. Returns the new row id."""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO managed_option_positions
               (subscriber_email, order_id, underlying, occ_symbol, expiry, strike,
                opt_type, qty, entry_price, stop_loss_pct, trail_trigger_pct, trail_pct)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (subscriber_email, order_id, underlying, occ_symbol, expiry, float(strike),
             opt_type.upper(), int(qty), float(entry_price),
             float(stop_loss_pct), float(trail_trigger_pct), float(trail_pct)),
        )
        return cur.lastrowid


def get_active_managed_options() -> list:
    """Return all rows with status='active' (used by the monitor loop)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM managed_option_positions WHERE status='active'",
        ).fetchall()
    return [dict(r) for r in rows]


def get_subscriber_managed_options(subscriber_email: str) -> list:
    """Return all managed option rows for a subscriber, newest first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM managed_option_positions WHERE subscriber_email=? ORDER BY id DESC",
            (subscriber_email,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_managed_option_state(
    pos_id: int, trailing_active: bool, peak_price: float, trail_stop_price: float,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE managed_option_positions
               SET trailing_active=?, peak_price=?, trail_stop_price=?,
                   updated_at=datetime('now')
               WHERE id=?""",
            (1 if trailing_active else 0, float(peak_price), float(trail_stop_price), pos_id),
        )


def close_managed_option(pos_id: int, reason: str, close_order_id: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE managed_option_positions
               SET status=?, close_order_id=?, updated_at=datetime('now')
               WHERE id=?""",
            (reason, close_order_id, pos_id),
        )


def deactivate_managed_option(pos_id: int, subscriber_email: str) -> bool:
    """Mark a position as 'deactivated' by its owner. Returns True if row found."""
    with get_connection() as conn:
        cur = conn.execute(
            """UPDATE managed_option_positions SET status='deactivated', updated_at=datetime('now')
               WHERE id=? AND subscriber_email=? AND status='active'""",
            (pos_id, subscriber_email),
        )
    return cur.rowcount > 0
