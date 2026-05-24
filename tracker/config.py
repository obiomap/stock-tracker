import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

DEFAULT_CONFIG = {
    "watchlist": [
        # Mega-cap tech / AI
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
        # Tech & software
        "AMD", "ORCL", "CRM", "QCOM", "AVGO", "NFLX", "UBER",
        # Semiconductors
        "TSM", "MU", "INTC", "ASML", "AMAT", "MRVL", "ARM", "KLAC", "LRCX",
        # Healthcare
        "JNJ", "LLY", "UNH", "PFE", "ABBV", "MRK",
        # Financials
        "JPM", "V", "MA", "BRK-B", "GS",
        # Energy
        "XOM", "CVX", "NEE",
        # Consumer
        "WMT", "COST", "HD", "NKE", "MCD",
        # ETFs
        "SPY", "QQQ", "VTI", "IWM",
        # Crypto — Layer 1s
        "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD",
        "ADA-USD", "AVAX-USD", "TON-USD", "NEAR-USD", "APT-USD",
        "SUI-USD", "HBAR-USD", "XLM-USD", "ATOM-USD",
        # Layer 2s / DeFi
        "MATIC-USD", "ARB-USD", "OP-USD", "LINK-USD", "UNI-USD",
        # Meme coins
        "DOGE-USD", "SHIB-USD", "PEPE-USD", "WIF-USD",
        # Real Estate (REITs)
        "AMT", "PLD", "EQIX", "O", "VICI", "SPG",
        # Industrials
        "CAT", "BA", "GE", "HON", "UPS", "FDX", "LMT", "RTX",
        # High-growth / AI plays
        "PLTR", "IONQ", "RGTI", "QUBT", "QBTS", "SHOP",
    ],
    "stock_sectors": {},
    "industry_etfs": {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Energy": "XLE",
        "Consumer Discretionary": "XLY",
        "Industrials": "XLI",
        "Communication Services": "XLC",
    },
    "email": {
        "sender": "",
        "password": "",
        "recipient": "obiomap@gmail.com",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "enabled": False,
    },
    "sms": {
        "enabled": False,
        "twilio_sid": "",
        "twilio_token": "",
        "twilio_from": "",
    },
    "social": {
        "twitter": {
            "enabled": False,
            "api_key": "",
            "api_secret": "",
            "access_token": "",
            "access_secret": "",
        },
        "public_url": "",
    },
    "alerts": {
        "price_change_threshold": 3.0,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "earnings_alert_days": 3,
        "ml_confidence_threshold": 0.70,
        "volume_spike_ratio": 2.0,
    },
    "refresh_interval": 300,
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        merged = {**DEFAULT_CONFIG, **data}
        merged["email"]   = {**DEFAULT_CONFIG["email"],   **data.get("email", {})}
        merged["sms"]     = {**DEFAULT_CONFIG["sms"],     **data.get("sms", {})}
        merged["social"]  = {
            **DEFAULT_CONFIG["social"],
            **data.get("social", {}),
            "twitter": {
                **DEFAULT_CONFIG["social"]["twitter"],
                **data.get("social", {}).get("twitter", {}),
            },
        }
        merged["alerts"]  = {**DEFAULT_CONFIG["alerts"],  **data.get("alerts", {})}
        merged["industry_etfs"]  = {**DEFAULT_CONFIG["industry_etfs"],  **data.get("industry_etfs", {})}
        merged["stock_sectors"]  = {**DEFAULT_CONFIG["stock_sectors"],  **data.get("stock_sectors", {})}
        return merged
    return {k: (v.copy() if isinstance(v, dict) else v) for k, v in DEFAULT_CONFIG.items()}


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
