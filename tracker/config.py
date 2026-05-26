import json
import os
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
        "ADA-USD", "AVAX-USD", "TON-USD", "NEAR-USD", "APT21794-USD",
        "SUI20947-USD", "HBAR-USD", "XLM-USD", "ATOM-USD",
        # Layer 2s / DeFi
        "POL28321-USD", "ARB-USD", "OP-USD", "LINK-USD", "UNI7083-USD",
        "AAVE-USD", "MKR-USD", "LDO-USD", "CRV-USD", "GRT6719-USD",
        # AI / DePIN tokens
        "RENDER-USD", "FET-USD", "SEI-USD", "TAO22974-USD",
        # New ecosystems / RWA
        "TIA-USD", "WLD-USD", "JUP-USD", "ENA-USD", "ONDO-USD", "IMX10603-USD",
        # Gaming / Metaverse
        "SAND-USD", "MANA-USD", "AXS-USD", "CHZ-USD",
        # DeFi / cross-chain
        "INJ-USD", "RUNE-USD", "STX4847-USD",
        # Privacy / PoW alts
        "ZEC-USD", "KAS-USD",
        # Blue-chip alts
        "DOT-USD", "LTC-USD", "ALGO-USD", "ICP-USD", "VET-USD",
        # Meme coins
        "DOGE-USD", "SHIB-USD", "PEPE24478-USD", "WIF-USD", "BONK-USD", "FLOKI-USD",
        # Real Estate (REITs)
        "AMT", "PLD", "EQIX", "O", "VICI", "SPG",
        # Industrials / Defense
        "CAT", "BA", "GE", "HON", "UPS", "FDX", "LMT", "RTX",
        # Defense & Space Tech
        "LHX", "CACI", "LDOS", "AXON", "RKLB", "ASTS",
        # High-growth / AI plays
        "PLTR", "IONQ", "RGTI", "QUBT", "QBTS", "SHOP",
        "SMCI", "DDOG", "RBLX", "RDDT", "HIMS",
        # US Tech / AI additions
        "NOW", "ANET", "SNOW", "TTD", "APP", "MSTR", "SPOT", "DUOL", "CELH",
        # Cybersecurity
        "CRWD", "PANW", "NET", "ZS", "OKTA", "FTNT", "S",
        # Fintech
        "PYPL", "COIN", "HOOD", "SOFI", "AFRM",
        # Commodities & Bonds ETFs
        "GLD", "SLV", "GDX", "USO", "TLT", "DIA",
        # Consumer & Entertainment additions
        "DIS", "ABNB", "DASH", "KO", "PG", "SBUX",
        # Healthcare additions
        "ABT", "ISRG", "MDT", "BMY",
        # Financials additions
        "BAC", "WFC", "MS", "C", "SCHW",
        # Penny stocks with potential
        "SNDL", "ACB", "CRON",          # Cannabis
        "OCGN", "ATOS", "BNGO",         # Biotech
        "WKHS", "LCID", "NIO",          # EV / clean transport
        "CLOV", "SPCE", "MVIS",         # Speculative tech
        "BBAI", "SOUN", "KULR",         # AI / small-cap tech
        # Latin America
        "MELI", "VALE", "ITUB", "EWZ",
        # Asian Markets
        "TM", "SONY", "NTDOY", "HMC", "MUFG",          # Japan
        "BABA", "BIDU", "JD", "PDD", "TCEHY", "BYDDY", # China
        "INFY", "HDB", "IBN", "WIT",                    # India
        "SE", "GRAB",                                    # Southeast Asia
        "EWJ", "MCHI", "INDA", "EWY", "FXI",            # Asian ETFs
        "KWEB", "EWT", "EWA",                            # More Asian/Pacific ETFs
        # European Markets
        "HSBC", "SHEL", "AZN", "BP", "GSK", "UL", "RIO",  # UK
        "SAP", "DB", "SIEGY",                               # Germany
        "LVMUY", "TTE", "EADSY",                            # France
        "NVS", "NSRGY",                                     # Switzerland
        "BHP",                                              # Australia (dual-listed London)
        "VGK", "EZU", "EWU",                                # European ETFs
        # Europe additions
        "NVO", "RACE", "STLA", "STM", "ING", "NOK",        # Pharma, Luxury, Auto, Chips, Banking, Telecom
        # African Markets
        "MTNOY", "NPSNY",                                   # MTN Group (SA), Naspers/Prosus (SA)
        # Global / Emerging Market ETFs
        "VWO", "KSA",
        # Nigerian / African stocks (London-listed, Yahoo Finance supported)
        "AAF.L", "SEPL.L",
        # Thematic & Leveraged ETFs
        "SOXL", "TQQQ", "UPRO",                             # Leveraged (3x Semis, QQQ, S&P 500)
        "ICLN", "LIT", "DRIV",                              # Clean energy, Lithium/Battery, EV/Auto
        "SKYY", "CLOU", "AIQ",                              # Cloud computing, AI & Tech ETFs
        "JETS", "XBI", "HACK",                              # Airlines, Biotech, Cybersecurity ETFs
        # US Large Cap additions
        "SNAP", "F", "GM", "CSCO", "IBM",                  # Social media, Auto, Networking, Enterprise tech
        "DELL", "ZM", "PINS", "LYFT", "ETSY",              # PC/Cloud, Videoconf, Social, Rideshare, eCommerce
        # Dividend & Value
        "MO", "T", "VZ", "PEP", "MMM",                     # Tobacco, Telecom, Telecom, Beverages, Industrials
        "D", "SO", "DUK", "CL", "MDLZ",                    # Utilities, Utilities, Utilities, Consumer staples
        # Dividend & Value additions
        "ENB", "BCE", "BTI", "PM",                          # Pipelines, Canadian Telecom, Tobacco, Tobacco
        "OKE", "WPC", "EPD", "ES", "AEP", "EXC",           # Midstream, REIT, Pipelines, Utilities x3
        # US Tech & Growth additions
        "TOST", "GTLB", "RELY",                             # Restaurant OS, DevSecOps, Remittance fintech
        # Healthcare & Biotech additions
        "HCA", "CI", "CVS",                                 # Hospital systems, Health insurance, Pharmacy
        # High-growth Biotech additions
        "VRTX", "BIIB", "ILMN", "DXCM", "GEHC", "INCY",   # Vertex, Biogen, Illumina, Dexcom, GE HealthCare, Incyte
        # Commodities & Mining
        "FCX", "AA", "CLF", "NEM", "AEM",                  # Copper, Aluminium, Steel, Gold miners
        "WPM", "GOLD", "MP", "RS",                          # Silver streams, Gold, Rare earth, Metals dist.
        # Nuclear & Energy Transition
        "CEG", "VST", "NRG",                                # Power generators (nuclear + gas, AI data center demand)
        "CCJ", "LEU",                                       # Uranium miners
        # AI Infrastructure
        "HPE", "NTAP", "PSTG",                              # Servers, storage, all-flash arrays
        # Defense Primes
        "NOC", "GD", "HII",                                 # Northrop, General Dynamics, Huntington Ingalls
        # Fintech additions
        "UPST",                                             # Upstart — AI-powered consumer lending platform
        # Small-Cap Growth / Aerospace
        "LUNR", "JOBY", "ACHR",                             # Lunar missions, eVTOL air taxis
        # Medical Devices
        "BSX", "SYK", "PODD",                               # Boston Scientific, Stryker, Insulet
        # Insurance
        "PGR", "CB", "AFL", "MET",                          # Progressive, Chubb, Aflac, MetLife
        # Digital Banking / LatAm
        "NU", "GLOB",                                        # Nubank, Globant
        # AI & Automation Software
        "PATH", "MNDY",                                      # UiPath, Monday.com
        # Pharma / Biotech gaps
        "REGN", "MRNA", "GILD",                             # Regeneron, Moderna, Gilead
        # Consumer / Retail gaps
        "LULU", "TJX", "MNST",                              # Lululemon, TJ Maxx, Monster Beverage
        # Natural Gas pure plays
        "EQT", "AR",                                         # EQT Corp, Antero Resources
    ],
    "stock_sectors": {
        # Cybersecurity
        "CRWD": "Cybersecurity", "PANW": "Cybersecurity", "NET":  "Cybersecurity",
        "ZS":   "Cybersecurity", "OKTA": "Cybersecurity", "FTNT": "Cybersecurity",
        "S":    "Cybersecurity",
        # Fintech
        "PYPL": "Fintech", "COIN": "Fintech",
        "HOOD": "Fintech", "SOFI": "Fintech", "AFRM": "Fintech",
        # Commodities & Bonds
        "GLD": "Commodities & Bonds", "SLV": "Commodities & Bonds",
        "GDX": "Commodities & Bonds", "USO": "Commodities & Bonds",
        "TLT": "Commodities & Bonds", "DIA": "Commodities & Bonds",
        # Consumer additions
        "DIS":  "Consumer", "ABNB": "Consumer", "DASH": "Consumer",
        "KO":   "Consumer", "PG":   "Consumer", "SBUX": "Consumer",
        # Healthcare additions
        "ABT":  "Healthcare & Biotech", "ISRG": "Healthcare & Biotech",
        "MDT":  "Healthcare & Biotech", "BMY":  "Healthcare & Biotech",
        # Financials additions
        "BAC":  "Financials", "WFC": "Financials", "MS": "Financials",
        "C":    "Financials", "SCHW": "Financials",
        # Tech additions
        "SMCI": "Technology", "DDOG": "Technology",
        "RBLX": "Technology", "RDDT": "Technology", "HIMS": "Technology",
        # US Tech / AI additions
        "NOW":  "Technology", "ANET": "Technology", "SNOW": "Technology",
        "TTD":  "Technology", "APP":  "Technology", "MSTR": "Technology",
        "SPOT": "Consumer",   "DUOL": "Technology", "CELH": "Consumer",
        # Latin America
        "MELI": "Latin America", "VALE": "Latin America",
        "ITUB": "Latin America", "EWZ":  "Latin America",
        # Southeast Asia
        "SE":   "Asian Markets", "GRAB": "Asian Markets",
        # Asian / Pacific ETFs
        "KWEB": "Asian Markets", "EWT":  "Asian Markets", "EWA": "Asian Markets",
        # European additions
        "BHP":  "European Markets",
        # Global / Emerging Market ETFs
        "VWO":  "ETFs", "KSA":  "ETFs",
        # Crypto — Gaming / Metaverse
        "SAND-USD":  "Cryptocurrency", "MANA-USD":  "Cryptocurrency",
        "AXS-USD":   "Cryptocurrency", "CHZ-USD":   "Cryptocurrency",
        # Crypto — DeFi / cross-chain
        "INJ-USD":   "Cryptocurrency", "RUNE-USD":  "Cryptocurrency",
        "STX4847-USD": "Cryptocurrency",
        # Crypto — Privacy / PoW alts
        "ZEC-USD":   "Cryptocurrency", "KAS-USD":   "Cryptocurrency",
        # Crypto — Layer 1s (blue-chip alts)
        "DOT-USD":       "Cryptocurrency", "LTC-USD":      "Cryptocurrency",
        "ALGO-USD":      "Cryptocurrency", "ICP-USD":      "Cryptocurrency",
        "VET-USD":       "Cryptocurrency",
        "APT21794-USD":  "Cryptocurrency", "SUI20947-USD": "Cryptocurrency",
        # Crypto — Layer 2s / DeFi
        "POL28321-USD":  "Cryptocurrency", "ARB-USD":      "Cryptocurrency",
        "OP-USD":        "Cryptocurrency", "LINK-USD":     "Cryptocurrency",
        "UNI7083-USD":   "Cryptocurrency", "AAVE-USD":     "Cryptocurrency",
        "MKR-USD":       "Cryptocurrency", "LDO-USD":      "Cryptocurrency",
        "CRV-USD":       "Cryptocurrency", "GRT6719-USD":  "Cryptocurrency",
        # Crypto AI/DePIN
        "RENDER-USD":    "Cryptocurrency", "FET-USD":      "Cryptocurrency",
        "SEI-USD":       "Cryptocurrency", "TAO22974-USD": "Cryptocurrency",
        # Crypto — New ecosystems / RWA
        "TIA-USD":       "Cryptocurrency", "WLD-USD":      "Cryptocurrency",
        "JUP-USD":       "Cryptocurrency", "ENA-USD":      "Cryptocurrency",
        "ONDO-USD":      "Cryptocurrency", "IMX10603-USD": "Cryptocurrency",
        # Crypto — Meme coins
        "PEPE24478-USD": "Cryptocurrency",
        "BONK-USD":      "Cryptocurrency", "FLOKI-USD":    "Cryptocurrency",
        # Penny stocks sector mapping
        "SNDL": "Penny Stocks", "ACB": "Penny Stocks", "CRON": "Penny Stocks",
        "OCGN": "Penny Stocks", "ATOS": "Penny Stocks", "BNGO": "Penny Stocks",
        "WKHS": "Penny Stocks", "LCID": "Penny Stocks", "NIO":  "Penny Stocks",
        "CLOV": "Penny Stocks", "SPCE": "Penny Stocks", "MVIS": "Penny Stocks",
        "BBAI": "Penny Stocks", "SOUN": "Penny Stocks", "KULR": "Penny Stocks",
        # Nigerian Exchange (NGX) - London-listed
        "AAF.L": "Nigerian Exchange (NGX)", "SEPL.L": "Nigerian Exchange (NGX)",
        # Asian Markets
        "TM": "Asian Markets", "SONY": "Asian Markets", "NTDOY": "Asian Markets",
        "HMC": "Asian Markets", "MUFG": "Asian Markets",
        "BABA": "Asian Markets", "BIDU": "Asian Markets", "JD": "Asian Markets",
        "PDD": "Asian Markets", "TCEHY": "Asian Markets", "BYDDY": "Asian Markets",
        "INFY": "Asian Markets", "HDB": "Asian Markets", "IBN": "Asian Markets",
        "WIT": "Asian Markets",
        "EWJ": "Asian Markets", "MCHI": "Asian Markets", "INDA": "Asian Markets",
        "EWY": "Asian Markets", "FXI": "Asian Markets",
        # European Markets
        "HSBC": "European Markets", "SHEL": "European Markets", "AZN": "European Markets",
        "BP": "European Markets", "GSK": "European Markets", "UL": "European Markets",
        "RIO": "European Markets", "SAP": "European Markets", "DB": "European Markets",
        "SIEGY": "European Markets", "LVMUY": "European Markets", "TTE": "European Markets",
        "EADSY": "European Markets", "NVS": "European Markets", "NSRGY": "European Markets",
        "VGK": "European Markets", "EZU": "European Markets", "EWU": "European Markets",
        # Europe additions
        "NVO":   "European Markets", "RACE":  "European Markets",
        "STLA":  "European Markets", "STM":   "European Markets",
        "ING":   "European Markets", "NOK":   "European Markets",
        # African Markets
        "MTNOY": "African Markets", "NPSNY": "African Markets",
        # Thematic & Leveraged ETFs
        "SOXL":  "ETFs", "TQQQ":  "ETFs", "UPRO":  "ETFs",
        "ICLN":  "ETFs", "LIT":   "ETFs", "DRIV":  "ETFs",
        "SKYY":  "ETFs", "CLOU":  "ETFs", "AIQ":   "ETFs",
        "JETS":  "ETFs", "XBI":   "ETFs", "HACK":  "ETFs",
        # US Large Cap additions
        "SNAP":  "Technology", "F":    "Consumer", "GM":   "Consumer",
        "CSCO":  "Technology", "IBM":  "Technology",
        "DELL":  "Technology", "ZM":   "Technology", "PINS": "Technology",
        "LYFT":  "Consumer",   "ETSY": "Consumer",
        # Dividend & Value
        "MO":    "Dividend & Value", "T":    "Dividend & Value",
        "VZ":    "Dividend & Value", "PEP":  "Dividend & Value",
        "MMM":   "Dividend & Value", "D":    "Dividend & Value",
        "SO":    "Dividend & Value", "DUK":  "Dividend & Value",
        "CL":    "Dividend & Value", "MDLZ": "Dividend & Value",
        "ENB":   "Dividend & Value", "BCE":  "Dividend & Value",
        "BTI":   "Dividend & Value", "PM":   "Dividend & Value",
        "OKE":   "Dividend & Value", "WPC":  "Dividend & Value",
        "EPD":   "Dividend & Value", "ES":   "Dividend & Value",
        "AEP":   "Dividend & Value", "EXC":  "Dividend & Value",
        # US Tech & Growth additions
        "TOST":  "Technology", "GTLB": "Technology", "RELY": "Fintech",
        # Healthcare additions
        "HCA":   "Healthcare & Biotech", "CI": "Healthcare & Biotech",
        "CVS":   "Healthcare & Biotech",
        # Defense & Space Tech
        "LHX":   "Industrials", "CACI":  "Industrials", "LDOS":  "Industrials",
        "AXON":  "Industrials", "RKLB":  "Industrials", "ASTS":  "Industrials",
        # High-growth Biotech
        "VRTX":  "Healthcare & Biotech", "BIIB":  "Healthcare & Biotech",
        "ILMN":  "Healthcare & Biotech", "DXCM":  "Healthcare & Biotech",
        "GEHC":  "Healthcare & Biotech", "INCY":  "Healthcare & Biotech",
        # Commodities & Mining
        "FCX":   "Commodities & Mining", "AA":   "Commodities & Mining",
        "CLF":   "Commodities & Mining", "NEM":  "Commodities & Mining",
        "AEM":   "Commodities & Mining", "WPM":  "Commodities & Mining",
        "GOLD":  "Commodities & Mining", "MP":   "Commodities & Mining",
        "RS":    "Commodities & Mining",
        # Nuclear & Energy Transition
        "CEG":   "Energy & Clean Energy", "VST":  "Energy & Clean Energy",
        "NRG":   "Energy & Clean Energy",
        "CCJ":   "Commodities & Mining",  "LEU":  "Commodities & Mining",
        # AI Infrastructure
        "HPE":   "Technology", "NTAP":  "Technology", "PSTG":  "Technology",
        # Defense Primes
        "NOC":   "Industrials", "GD":   "Industrials", "HII":   "Industrials",
        # Fintech
        "UPST":  "Fintech",
        # Small-Cap Growth / Aerospace
        "LUNR":  "Industrials", "JOBY":  "Industrials", "ACHR":  "Industrials",
        # Medical Devices
        "BSX":   "Healthcare & Biotech", "SYK":  "Healthcare & Biotech",
        "PODD":  "Healthcare & Biotech",
        # Insurance
        "PGR":   "Financials", "CB":    "Financials",
        "AFL":   "Financials", "MET":   "Financials",
        # Digital Banking / LatAm
        "NU":    "Fintech", "GLOB":  "Latin America",
        # AI & Automation Software
        "PATH":  "AI & Machine Learning", "MNDY":  "Technology",
        # Pharma / Biotech gaps
        "REGN":  "Healthcare & Biotech", "MRNA":  "Healthcare & Biotech",
        "GILD":  "Healthcare & Biotech",
        # Consumer / Retail gaps
        "LULU":  "Consumer", "TJX":   "Consumer", "MNST":  "Consumer",
        # Natural Gas pure plays
        "EQT":   "Energy & Clean Energy", "AR":   "Energy & Clean Energy",
    },
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
        _apply_env_overrides(merged)
        return merged
    base = {k: (v.copy() if isinstance(v, dict) else v) for k, v in DEFAULT_CONFIG.items()}
    _apply_env_overrides(base)
    return base


def _apply_env_overrides(config: dict) -> None:
    """Override email/SMS/Resend settings from environment variables (used on Railway)."""
    email = config.setdefault("email", {})
    if os.environ.get("EMAIL_SENDER"):
        email["sender"] = os.environ["EMAIL_SENDER"]
    if os.environ.get("EMAIL_PASSWORD"):
        email["password"] = os.environ["EMAIL_PASSWORD"]
    if os.environ.get("EMAIL_RECIPIENT"):
        email["recipient"] = os.environ["EMAIL_RECIPIENT"]
    if os.environ.get("EMAIL_ENABLED"):
        email["enabled"] = os.environ["EMAIL_ENABLED"].lower() in ("1", "true", "yes")

    # Resend
    if os.environ.get("RESEND_API_KEY"):
        config["resend_api_key"] = os.environ["RESEND_API_KEY"]
    if os.environ.get("RESEND_FROM"):
        config["resend_from"] = os.environ["RESEND_FROM"]

    # Twilio SMS
    sms = config.setdefault("sms", {})
    if os.environ.get("TWILIO_ACCOUNT_SID"):
        sms["twilio_sid"] = os.environ["TWILIO_ACCOUNT_SID"]
    if os.environ.get("TWILIO_AUTH_TOKEN"):
        sms["twilio_token"] = os.environ["TWILIO_AUTH_TOKEN"]
    if os.environ.get("TWILIO_FROM_NUMBER"):
        sms["twilio_from"] = os.environ["TWILIO_FROM_NUMBER"]
    if sms.get("twilio_sid") and sms.get("twilio_token") and sms.get("twilio_from"):
        sms["enabled"] = True


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
