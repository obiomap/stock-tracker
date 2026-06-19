"""Background monitor for managed option positions.

For each managed position:
  - If P&L drops to -20%  → sell to close (stop-loss)
  - If P&L rises to +20%  → activate 5% trailing stop
  - While trailing active  → track peak; if price falls 5% from peak → sell to close
"""

import threading
import time
import logging
from datetime import datetime

log = logging.getLogger(__name__)

POLL_SECONDS = 30


def _eastern_now():
    try:
        import pytz
        return datetime.now(pytz.timezone("US/Eastern"))
    except Exception:
        return datetime.utcnow()


def _market_open() -> bool:
    now = _eastern_now()
    if now.weekday() >= 5:
        return False
    return (9, 30) <= (now.hour, now.minute) < (16, 0)


def _current_bid(underlying: str, expiry: str, strike: float, opt_type: str) -> float | None:
    """Return best exit price (bid) for the contract, or None on failure."""
    try:
        from . import broker as _broker
        q = _broker.get_option_quote(underlying, expiry, strike, opt_type)
        if not q.get("ok"):
            return None
        bid = float(q.get("bid") or 0)
        last = float(q.get("last") or 0)
        return bid if bid > 0 else (last if last > 0 else None)
    except Exception:
        return None


def _close_position(pos: dict, current_price: float, reason: str) -> None:
    from . import broker as _broker, database as db

    occ_sym = pos["occ_symbol"]
    qty = int(pos["qty"])
    underlying = pos["underlying"]
    subscriber = pos["subscriber_email"]

    result = _broker.close_option_position(occ_sym, qty, current_price)
    close_id = result.get("id", "") if result.get("ok") else ""

    db.close_managed_option(pos["id"], reason, close_id)
    if close_id:
        db.record_subscriber_order(close_id, subscriber, underlying)

    log.info(
        "Managed option %s closed: reason=%s price=%.4f order=%s",
        occ_sym, reason, current_price, close_id,
    )


def _process(pos: dict) -> None:
    current = _current_bid(
        pos["underlying"], pos["expiry"], float(pos["strike"]), pos["opt_type"]
    )
    if not current or current <= 0:
        return

    entry = float(pos["entry_price"])
    pnl_pct = (current - entry) / entry * 100.0

    stop_loss_pct   = float(pos["stop_loss_pct"])    # default 20
    trail_trigger   = float(pos["trail_trigger_pct"]) # default 20
    trail_pct       = float(pos["trail_pct"])          # default 5
    trailing_active = bool(pos["trailing_active"])
    peak = float(pos["peak_price"] or current)
    pos_id = int(pos["id"])

    from . import database as db

    # ── Stop-loss ──────────────────────────────────────────────────────────
    if pnl_pct <= -stop_loss_pct:
        _close_position(pos, current, "stop_loss")
        return

    # ── Activate trailing stop ─────────────────────────────────────────────
    if not trailing_active and pnl_pct >= trail_trigger:
        trail_stop = current * (1 - trail_pct / 100.0)
        db.update_managed_option_state(pos_id, True, current, trail_stop)
        log.info(
            "Trailing stop activated for managed option %s  peak=%.4f stop=%.4f",
            pos["occ_symbol"], current, trail_stop,
        )
        return

    # ── Update trailing stop ───────────────────────────────────────────────
    if trailing_active:
        if current > peak:
            peak = current
        trail_stop = peak * (1 - trail_pct / 100.0)
        db.update_managed_option_state(pos_id, True, peak, trail_stop)

        if current <= trail_stop:
            _close_position(pos, current, "trailing_stop")


def _monitor_loop() -> None:
    while True:
        time.sleep(POLL_SECONDS)
        if not _market_open():
            continue
        try:
            from . import database as db
            for pos in db.get_active_managed_options():
                try:
                    _process(pos)
                except Exception as exc:
                    log.exception("Error processing managed option id=%s: %s", pos.get("id"), exc)
        except Exception as exc:
            log.exception("option_manager loop error: %s", exc)


def start() -> None:
    threading.Thread(target=_monitor_loop, daemon=True, name="option-manager").start()
    log.info("Option manager monitor started (poll every %ds)", POLL_SECONDS)
