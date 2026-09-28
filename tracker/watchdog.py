"""
watchdog.py -- Liveness watchdog that exits the process when it goes bad.

Railway only calls the healthcheck path during a deploy; once live, nothing
restarts a process that is still running but no longer serving. Twice
(2026-09-13, 2026-09-27) the app sat pinned at its 8GB memory cap for 1-2
days, "Online" but returning 502s. This thread exits the process instead,
and Railway's ON_FAILURE restart policy brings up a fresh one.

Trips on either:
  - RSS above WATCHDOG_MAX_RSS_MB (default 7000, below the 8GB cap so we
    exit before the heap starts thrashing)
  - WATCHDOG_FAILS consecutive failed GETs of our own /health endpoint
"""
import os
import threading
import time
import urllib.request

_CHECK_EVERY_S = 60
_GRACE_S       = 300   # startup refresh/training can be slow; don't probe yet
_PROBE_TIMEOUT = 15


def _rss_mb() -> float | None:
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except OSError:
        pass
    return None   # not Linux -- memory check disabled


def _die(reason: str) -> None:
    print(f"[watchdog] {reason} -- exiting so the platform restarts us", flush=True)
    os._exit(1)


def start(health_url: str) -> None:
    """Start the watchdog thread. No-op when WATCHDOG_DISABLE is set."""
    if os.environ.get("WATCHDOG_DISABLE"):
        return
    max_rss   = float(os.environ.get("WATCHDOG_MAX_RSS_MB", 7000))
    max_fails = int(os.environ.get("WATCHDOG_FAILS", 5))

    def _loop() -> None:
        started = time.time()
        fails = 0
        while True:
            time.sleep(_CHECK_EVERY_S)
            rss = _rss_mb()
            if rss is not None and rss > max_rss:
                _die(f"RSS {rss:.0f}MB > {max_rss:.0f}MB")
            if time.time() - started < _GRACE_S:
                continue
            try:
                with urllib.request.urlopen(health_url, timeout=_PROBE_TIMEOUT) as r:
                    ok = r.status == 200
            except Exception:
                ok = False
            fails = 0 if ok else fails + 1
            if fails:
                print(f"[watchdog] health probe failed ({fails}/{max_fails})", flush=True)
            if fails >= max_fails:
                _die(f"{fails} consecutive failed health probes")

    threading.Thread(target=_loop, daemon=True, name="watchdog").start()
