"""
Social media integration for subscriber acquisition.

Twitter/X: configure API credentials via 'run.bat setup'.
Share buttons: work without API — generate intent URLs for one-click sharing.
"""
from __future__ import annotations
import urllib.parse
from datetime import datetime


# ── share URL generators (no API required) ───────────────────────────────────

def twitter_intent_url(text: str, url: str = "") -> str:
    params = {"text": text}
    if url:
        params["url"] = url
    return "https://twitter.com/intent/tweet?" + urllib.parse.urlencode(params)


def linkedin_share_url(url: str, title: str = "") -> str:
    params = {"url": url}
    if title:
        params["title"] = title
    return "https://www.linkedin.com/shareArticle?" + urllib.parse.urlencode(params)


def facebook_share_url(url: str) -> str:
    return "https://www.facebook.com/sharer/sharer.php?" + urllib.parse.urlencode({"u": url})


# ── post text generators ──────────────────────────────────────────────────────

def generate_subscribe_post(public_url: str, watchlist: list[str]) -> str:
    syms = " ".join(f"${s.replace('-USD','')}" for s in watchlist[:6])
    return (
        f"Get free AI-powered stock + crypto alerts for {syms} and more.\n"
        f"Signals include RSI, MACD, earnings dates, and ML predictions.\n"
        f"Subscribe free: {public_url}\n"
        f"#stocks #crypto #investing #stockmarket #pennystock"
    )


def generate_market_post(stocks: list[dict], public_url: str = "") -> str:
    """Create a market-update post highlighting top movers."""
    if not stocks:
        return ""

    movers = sorted(stocks, key=lambda s: abs(s.get("change_pct") or 0), reverse=True)[:4]
    lines = []
    for s in movers:
        sym = s["symbol"].replace("-USD", "")
        chg = s.get("change_pct") or 0
        sig = s.get("prediction", "")
        arrow = "+" if chg >= 0 else ""
        signal_tag = f" [{sig}]" if sig and sig != "NEUTRAL" else ""
        lines.append(f"${sym} {arrow}{chg:.1f}%{signal_tag}")

    movers_text = " | ".join(lines)
    now = datetime.now().strftime("%b %d")
    post = f"Market update {now}: {movers_text}"
    if public_url:
        post += f"\nFree alerts: {public_url}"
    post += "\n#stocks #trading #stockmarket"
    return post[:280]  # Twitter character limit


# ── Twitter/X API posting ─────────────────────────────────────────────────────

def _twitter_ready(config: dict) -> bool:
    tw = config.get("social", {}).get("twitter", {})
    return all([tw.get("api_key"), tw.get("api_secret"),
                tw.get("access_token"), tw.get("access_secret")])


def post_to_twitter(text: str, config: dict) -> bool:
    """Post a tweet via Twitter API v2 (requires Tweepy + API credentials)."""
    if not _twitter_ready(config):
        return False
    try:
        import tweepy
        tw = config["social"]["twitter"]
        client = tweepy.Client(
            consumer_key=tw["api_key"],
            consumer_secret=tw["api_secret"],
            access_token=tw["access_token"],
            access_token_secret=tw["access_secret"],
        )
        client.create_tweet(text=text[:280])
        return True
    except Exception as e:
        print(f"[Twitter] {e}")
        return False


def post_market_update(stocks: list[dict], config: dict) -> bool:
    """Generate and post a market update tweet."""
    public_url = config.get("social", {}).get("public_url", "")
    text = generate_market_post(stocks, public_url)
    if not text:
        return False
    return post_to_twitter(text, config)


def post_subscribe_cta(config: dict, watchlist: list[str]) -> bool:
    """Post a subscribe call-to-action tweet."""
    public_url = config.get("social", {}).get("public_url", "")
    if not public_url:
        return False
    text = generate_subscribe_post(public_url, watchlist)
    return post_to_twitter(text, config)
