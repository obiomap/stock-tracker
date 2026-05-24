"""
Sector catalog: predefined categories, their stocks, and dashboard colors.
"""

SECTOR_COLORS: dict[str, str] = {
    "AI & Machine Learning":  "bright_magenta",
    "Technology":             "bright_cyan",
    "Semiconductors":         "bright_yellow",
    "Healthcare & Biotech":   "bright_green",
    "Quantum Computing":      "medium_purple1",
    "ETFs":                   "bright_white",
    "Financials":             "gold1",
    "Energy & Clean Energy":  "orange3",
    "Consumer":               "sky_blue2",
    "Real Estate":            "deep_sky_blue1",
    "Industrials":            "sandy_brown",
    "Penny Stocks":           "orange_red1",
    "Cryptocurrency":         "bright_yellow",
    "Asian Markets":          "red1",
    "European Markets":       "cornflower_blue",
    "Nigerian Exchange (NGX)":"green3",
    "General":                "white",
}

SECTOR_CATALOG: dict[str, dict] = {
    "AI & Machine Learning": {
        "description": "Companies building or deploying large-scale AI/ML models and infrastructure.",
        "key_drivers": [
            "GPU and cloud compute demand",
            "Foundation model releases (GPT, Gemini, Claude)",
            "Enterprise AI adoption rate",
            "AI chip export regulations",
        ],
        "stocks": {
            "NVDA": "AI GPU market leader — ~80% data center market share",
            "MSFT": "Azure OpenAI, Copilot across Office and Windows",
            "GOOGL": "Gemini, DeepMind, custom TPU infrastructure",
            "META": "LLaMA open-source models, AI-powered ad targeting",
            "AMZN": "AWS Bedrock AI platform, Alexa+, Trainium chips",
            "PLTR": "Palantir — AI analytics for enterprise and defense",
            "AI":   "C3.ai — enterprise AI software applications",
            "SOUN": "SoundHound — voice AI for automotive and restaurants",
            "BBAI": "BigBear.ai — defense and intelligence AI",
        },
    },
    "Technology": {
        "description": "Established software, cloud, and hardware platform companies.",
        "key_drivers": [
            "Cloud adoption and migration spending",
            "Enterprise software renewal cycles",
            "Consumer hardware upgrade cycles",
            "Interest rates (affect growth valuations)",
        ],
        "stocks": {
            "AAPL":  "iPhone, Mac, iPad ecosystem + App Store",
            "ORCL":  "Cloud databases and enterprise applications",
            "CRM":   "Salesforce — CRM + AI Einstein layer",
            "IBM":   "Enterprise AI, hybrid cloud, quantum research",
            "INTC":  "Intel — legacy CPU leader losing share to AMD",
            "AMD":   "Challenging Intel on CPUs; NVDA on data center GPUs",
            "QCOM":  "Mobile chipsets and growing automotive chips",
            "SNOW":  "Snowflake — cloud data platform and sharing",
            "SHOP":  "Shopify — global e-commerce infrastructure",
            "NOW":   "ServiceNow — enterprise workflow automation + AI",
            "NFLX":  "Netflix — streaming leader with ad-supported tier and gaming",
        },
    },
    "Semiconductors": {
        "description": "Chip designers, manufacturers, and equipment makers — backbone of the digital economy.",
        "key_drivers": [
            "AI training and inference chip demand",
            "PC/smartphone unit volumes",
            "US-China export restrictions",
            "Fab capex cycles (multi-year buildout)",
        ],
        "stocks": {
            "NVDA": "AI GPUs + gaming — most valued semiconductor company",
            "AMD":  "Ryzen CPUs and Instinct data center GPUs",
            "INTC": "Intel — Xeon server chips + Intel Foundry ambitions",
            "QCOM": "Snapdragon mobile SoCs and automotive",
            "TSM":  "TSMC — world's largest advanced chip foundry",
            "ASML": "Only maker of EUV lithography machines (monopoly)",
            "MU":   "Micron — DRAM and NAND flash memory",
            "AMAT": "Applied Materials — chip fab equipment leader",
            "AVGO": "Broadcom — networking chips + custom AI ASICs",
            "MRVL": "Marvell — cloud data infrastructure chips",
            "ARM":  "ARM Holdings — CPU architecture powering 99% of smartphones",
            "KLAC": "KLA Corporation — semiconductor process control equipment",
            "LRCX": "Lam Research — etch and deposition equipment for chip fabs",
            "ON":   "ON Semiconductor — chips for EVs and industrial automation",
            "WOLF": "Wolfspeed — silicon carbide chips for EVs and power grid",
        },
    },
    "Healthcare & Biotech": {
        "description": "Drug makers, insurers, and medical device companies.",
        "key_drivers": [
            "FDA approval/rejection decisions",
            "Drug pricing legislation",
            "Clinical trial results",
            "Healthcare utilization trends",
        ],
        "stocks": {
            "JNJ":  "Johnson & Johnson — diversified healthcare",
            "LLY":  "Eli Lilly — GLP-1 obesity drugs (Mounjaro, Zepbound)",
            "UNH":  "UnitedHealth — largest US health insurer",
            "PFE":  "Pfizer — large pharma, post-COVID pipeline rebuild",
            "ABBV": "AbbVie — Humira successor Skyrizi/Rinvoq",
            "MRK":  "Merck — Keytruda cancer immunotherapy leader",
            "AMGN": "Amgen — biopharmaceuticals and biosimilars",
            "GILD": "Gilead — antiviral drugs and oncology",
            "MRNA": "Moderna — mRNA technology platform",
            "REGN": "Regeneron — Dupixent and EYLEA flagship drugs",
        },
    },
    "Quantum Computing": {
        "description": "Early-stage companies and research arms building quantum processors and software.",
        "key_drivers": [
            "Qubit error rate improvements",
            "Government and enterprise R&D contracts",
            "Breakthroughs in fault-tolerant computation",
            "Competition from classical HPC alternatives",
        ],
        "stocks": {
            "IONQ": "Trapped-ion quantum computers — hardware + cloud access",
            "RGTI": "Rigetti Computing — superconducting qubit systems",
            "QUBT": "Quantum Computing Inc — optimization software",
            "IBM":  "IBM Quantum — 1000+ qubit systems, Qiskit platform",
            "GOOGL":"Willow quantum chip — error correction milestone",
            "MSFT": "Azure Quantum — topological qubit research (Station Q)",
            "QBTS": "D-Wave Quantum — quantum annealing for optimization problems",
            "ARQQ": "Arqit Quantum — quantum encryption and cybersecurity",
        },
    },
    "ETFs": {
        "description": "Exchange-Traded Funds — baskets of stocks offering instant diversification.",
        "key_drivers": [
            "Broad market sentiment (SPY/QQQ follow macro closely)",
            "Sector rotation by institutional investors",
            "Interest rate environment (affects growth vs value)",
            "Expense ratio and liquidity (for trading cost)",
        ],
        "stocks": {
            "SPY":  "S&P 500 — top 500 US companies by market cap",
            "QQQ":  "Nasdaq-100 — 100 largest non-financial Nasdaq stocks",
            "IWM":  "Russell 2000 — 2000 small-cap US companies",
            "VTI":  "Vanguard Total Market — entire US equity market",
            "XLK":  "Technology Select Sector SPDR",
            "XLV":  "Healthcare Select Sector SPDR",
            "XLF":  "Financials Select Sector SPDR",
            "XLE":  "Energy Select Sector SPDR",
            "ARKK": "ARK Innovation — disruptive tech, high risk/reward",
            "SOXX": "iShares Semiconductor ETF",
            "BOTZ": "Global Robotics & AI ETF",
        },
    },
    "Financials": {
        "description": "Banks, payment networks, and investment firms.",
        "key_drivers": [
            "Federal Reserve interest rate decisions",
            "Credit default and loan loss rates",
            "Trading and investment banking volumes",
            "Regulatory capital requirements",
        ],
        "stocks": {
            "JPM":   "JPMorgan Chase — largest US bank by assets",
            "BAC":   "Bank of America — retail and commercial banking",
            "GS":    "Goldman Sachs — investment banking and trading",
            "V":     "Visa — largest global payment network",
            "MA":    "Mastercard — second largest payment network",
            "BRK-B": "Berkshire Hathaway — Buffett's diversified conglomerate",
            "WFC":   "Wells Fargo — consumer and commercial banking",
            "MS":    "Morgan Stanley — wealth management and investment banking",
        },
    },
    "Energy & Clean Energy": {
        "description": "Traditional oil & gas alongside solar, wind, and hydrogen companies.",
        "key_drivers": [
            "Crude oil and natural gas prices",
            "Renewable energy policy and subsidies (IRA Act)",
            "Global energy demand growth",
            "OPEC+ production decisions",
        ],
        "stocks": {
            "XOM":  "ExxonMobil — largest US integrated oil company",
            "CVX":  "Chevron — upstream exploration and downstream refining",
            "NEE":  "NextEra Energy — largest US wind and solar operator",
            "ENPH": "Enphase Energy — residential solar microinverters",
            "FSLR": "First Solar — utility-scale thin-film solar panels",
            "PLUG": "Plug Power — hydrogen fuel cells and electrolyzers",
        },
    },
    "Consumer": {
        "description": "Retail, food, and brand companies exposed to consumer spending trends.",
        "key_drivers": [
            "Consumer confidence and discretionary spending",
            "Inflation and cost of goods",
            "E-commerce adoption vs brick-and-mortar",
            "Employment and wage growth",
        ],
        "stocks": {
            "AMZN": "Amazon — e-commerce + AWS cloud + advertising",
            "WMT":  "Walmart — retail giant with fast-growing e-commerce",
            "COST": "Costco — membership warehouse with loyal customer base",
            "TGT":  "Target — discount retail, strong brand partnerships",
            "HD":   "Home Depot — home improvement market leader",
            "NKE":  "Nike — global athletic footwear and apparel",
            "MCD":  "McDonald's — global QSR franchise model",
            "UBER": "Uber — ride-hailing + food delivery + freight platform",
        },
    },
    "Penny Stocks": {
        "description": "High-risk, high-reward small-cap stocks under $10 with significant upside catalysts.",
        "key_drivers": [
            "Momentum and retail trader sentiment",
            "Contract wins and partnership announcements",
            "Revenue growth from near-zero base (% swings)",
            "Short squeeze potential and float size",
        ],
        "stocks": {
            "SOUN": "SoundHound AI — voice AI for restaurants and automotive",
            "BBAI": "BigBear.ai — AI analytics for defense and intelligence",
            "KULR": "KULR Technology — NASA-backed thermal/battery management",
            "LUNR": "Intuitive Machines — NASA lunar landing missions",
            "OPEN": "Opendoor Technologies — online real estate marketplace",
            "NKLA": "Nikola — hydrogen and electric semi-trucks",
            "MARA": "Marathon Digital — largest US publicly-traded Bitcoin miner",
            "CLSK": "CleanSpark — sustainable Bitcoin mining + clean energy",
            "RXRX": "Recursion Pharma — AI-powered drug discovery platform",
            "VFS":  "VinFast Auto — Vietnamese EV maker with global ambitions",
        },
    },
    "Real Estate": {
        "description": "REITs and real estate companies — income-focused, rate-sensitive assets that distribute 90%+ of income as dividends.",
        "key_drivers": [
            "Federal Reserve interest rate decisions (REITs move inversely with rates)",
            "Occupancy rates and rental income growth",
            "Commercial vs residential demand trends (office vs industrial vs retail)",
            "Cap rate spreads vs Treasury bond yields",
        ],
        "stocks": {
            "AMT":  "American Tower — global cell tower REIT (5G infrastructure backbone)",
            "PLD":  "Prologis — largest industrial/warehouse REIT (Amazon's key landlord)",
            "EQIX": "Equinix — data center REIT powering global internet infrastructure",
            "SPG":  "Simon Property Group — premium mall and outlet center REIT",
            "O":    "Realty Income — monthly dividend REIT, 1,000+ retail tenants",
            "CCI":  "Crown Castle — cell tower and small cell fiber network REIT",
            "VICI": "VICI Properties — casino and entertainment venue REIT (MGM, Caesars)",
            "DLR":  "Digital Realty — data center REIT for cloud and AI workloads",
            "WY":   "Weyerhaeuser — timberland REIT + wood products manufacturer",
            "PSA":  "Public Storage — largest self-storage REIT in the US",
        },
    },
    "Industrials": {
        "description": "Manufacturing, aerospace, defense, and logistics companies driving physical economic growth.",
        "key_drivers": [
            "US infrastructure spending and government defense budgets",
            "Global supply chain capacity and freight volumes",
            "Manufacturing PMI and factory order data",
            "Geopolitical tensions (defense spending) and trade tariffs",
        ],
        "stocks": {
            "CAT":  "Caterpillar — construction and mining equipment global leader",
            "BA":   "Boeing — commercial aircraft and defense (737 MAX + 787 Dreamliner)",
            "GE":   "GE Aerospace — jet engines for commercial and military aircraft",
            "HON":  "Honeywell — industrial automation, aerospace, and building tech",
            "UPS":  "UPS — global package delivery and supply chain logistics",
            "FDX":  "FedEx — express shipping and freight leader",
            "DE":   "John Deere — agricultural and construction equipment",
            "LMT":  "Lockheed Martin — F-35 fighter jets, missile systems, defense prime",
            "RTX":  "RTX (Raytheon) — missiles, radar systems, and commercial aerospace",
            "MMM":  "3M — diversified industrial products and adhesives conglomerate",
            "CSX":  "CSX — major US freight railroad operator",
            "NOC":  "Northrop Grumman — B-21 stealth bomber, space and cyber defense",
        },
    },
    "Asian Markets": {
        "description": "Top Asian equities — Japan, China, India, South Korea and regional ETFs.",
        "key_drivers": [
            "China economic data and PBOC policy",
            "Japan BOJ interest rate decisions",
            "India GDP growth and RBI policy",
            "US-China trade relations and tariffs",
            "Regional tech sector sentiment",
        ],
        "stocks": {
            # Japan
            "TM":    "Toyota — world's largest automaker by volume",
            "SONY":  "Sony — consumer electronics, gaming (PlayStation), entertainment",
            "NTDOY": "Nintendo — Switch console, Mario/Zelda IP, mobile gaming",
            "HMC":   "Honda — autos, motorcycles, and growing EV line-up",
            "MUFG":  "Mitsubishi UFJ — Japan's largest bank by assets",
            # China
            "BABA":  "Alibaba — China's e-commerce and cloud leader",
            "BIDU":  "Baidu — China's Google + autonomous driving (Apollo)",
            "JD":    "JD.com — China's second largest e-commerce platform",
            "PDD":   "PDD Holdings — Pinduoduo + Temu global e-commerce",
            "TCEHY": "Tencent — WeChat super-app, gaming, fintech (ADR)",
            "BYDDY": "BYD — world's #1 EV maker by volume (ADR)",
            # India
            "INFY":  "Infosys — India's second largest IT services firm",
            "HDB":   "HDFC Bank — India's largest private bank",
            "IBN":   "ICICI Bank — India's second largest private bank",
            "TTM":   "Tata Motors — Jaguar Land Rover + fast-growing EV arm",
            "WIT":   "Wipro — global IT services and consulting",
            # Regional ETFs
            "EWJ":   "iShares MSCI Japan ETF — broad Japan large-cap exposure",
            "MCHI":  "iShares MSCI China ETF — 600+ Chinese large/mid caps",
            "INDA":  "iShares MSCI India ETF — India's top 85% market-cap stocks",
            "EWY":   "iShares MSCI South Korea ETF — Samsung, SK Hynix, Hyundai",
            "FXI":   "iShares China Large-Cap ETF — 50 largest H-share Chinese stocks",
        },
    },
    "European Markets": {
        "description": "Leading European equities — UK, Germany, France, Switzerland and regional ETFs.",
        "key_drivers": [
            "ECB interest rate decisions",
            "EUR/USD exchange rate",
            "Germany industrial output and PMI",
            "UK Bank of England policy",
            "Energy prices (EU heavily import-dependent)",
        ],
        "stocks": {
            # United Kingdom
            "HSBC":  "HSBC — largest European bank, global trade finance hub",
            "SHEL":  "Shell — global energy major, LNG and renewables",
            "AZN":   "AstraZeneca — UK/Sweden pharma; oncology and vaccines",
            "BP":    "BP — integrated energy with growing renewables arm",
            "GSK":   "GSK — vaccines, HIV treatments, consumer health",
            "UL":    "Unilever — 400+ consumer brands (Dove, Hellmann's, Ben & Jerry's)",
            "RIO":   "Rio Tinto — global mining; iron ore, copper, lithium",
            # Germany
            "SAP":   "SAP — Europe's largest software firm; ERP and cloud",
            "DB":    "Deutsche Bank — Germany's largest lender",
            "SIEGY": "Siemens — industrial automation, smart infrastructure",
            # France
            "LVMUY": "LVMH — world's largest luxury group (Louis Vuitton, Dior)",
            "TTE":   "TotalEnergies — French oil & gas + top solar developer",
            "EADSY": "Airbus — world's largest commercial aircraft maker",
            # Switzerland
            "NVS":   "Novartis — global pharma; heart failure, eye care",
            "NSRGY": "Nestlé — world's largest food & beverage company",
            # Regional ETFs
            "VGK":   "Vanguard FTSE Europe ETF — 1,300+ European stocks",
            "EZU":   "iShares MSCI Eurozone ETF — 18-country eurozone exposure",
            "EWU":   "iShares MSCI United Kingdom ETF — FTSE large/mid caps",
        },
    },
    "Nigerian Exchange (NGX)": {
        "description": "Nigerian and African stocks London-listed on the LSE — accessible via Yahoo Finance with live prices.",
        "key_drivers": [
            "CBN monetary policy and naira exchange rate",
            "Oil price (Nigeria is Africa's top crude exporter)",
            "Pan-African mobile subscriber growth",
            "UK-listed ADR/GDR premium vs NGX spot",
            "Foreign portfolio investor flows into Africa",
        ],
        "stocks": {
            "AAF.L":  "Airtel Africa — pan-African telecoms and mobile money (14 countries)",
            "SEPL.L": "Seplat Energy — Nigeria's largest independent oil & gas producer",
        },
    },
    "Cryptocurrency": {
        "description": "Digital assets trading 24/7. High volatility, high potential. Macro + sentiment driven.",
        "key_drivers": [
            "Bitcoin ETF flows and institutional adoption",
            "Federal Reserve rate policy (risk-on/risk-off)",
            "Regulatory clarity (SEC, CFTC rulings)",
            "On-chain activity and developer ecosystem growth",
        ],
        "stocks": {
            # Layer 1s
            "BTC-USD":  "Bitcoin — digital gold, dominant store of value",
            "ETH-USD":  "Ethereum — smart contracts, DeFi, NFT platform",
            "SOL-USD":  "Solana — high-speed L1, top DeFi and meme coin chain",
            "XRP-USD":  "XRP (Ripple) — cross-border institutional payments",
            "ADA-USD":  "Cardano — proof-of-stake, peer-reviewed academic blockchain",
            "AVAX-USD": "Avalanche — sub-second finality DeFi ecosystem",
            "DOT-USD":  "Polkadot — cross-chain interoperability protocol",
            "ATOM-USD": "Cosmos — 'internet of blockchains' via IBC protocol",
            "NEAR-USD": "NEAR Protocol — sharded L1 with AI + blockchain focus",
            "APT-USD":  "Aptos — Move language L1 from ex-Meta Diem engineers",
            "SUI-USD":  "Sui — object-centric Move L1, high throughput",
            "TON-USD":  "Toncoin — Telegram's blockchain, 900M+ user access",
            "HBAR-USD": "Hedera — enterprise hashgraph, fast and energy-efficient",
            "XLM-USD":  "Stellar — cross-border payments, institutional focus",
            "ALGO-USD": "Algorand — pure proof-of-stake, carbon-negative chain",
            "VET-USD":  "VeChain — supply chain and enterprise blockchain",
            "ICP-USD":  "Internet Computer — decentralized cloud compute (Dfinity)",
            # Layer 2s / DeFi
            "MATIC-USD":"Polygon (POL) — Ethereum L2 scaling solution",
            "ARB-USD":  "Arbitrum — largest Ethereum L2 by total value locked",
            "OP-USD":   "Optimism — Ethereum L2 with Superchain multi-chain vision",
            "LINK-USD": "Chainlink — oracle network connecting blockchains to real-world data",
            "UNI-USD":  "Uniswap — governance token of the largest DEX by volume",
            "AAVE-USD": "Aave — leading decentralized lending and borrowing protocol",
            "MKR-USD":  "Maker — governs DAI stablecoin, oldest DeFi protocol",
            # Meme coins
            "DOGE-USD": "Dogecoin — original meme coin, Elon Musk favourite",
            "SHIB-USD": "Shiba Inu — meme coin ecosystem with ShibaSwap DEX",
            "PEPE-USD": "Pepe — largest frog-themed meme coin by market cap",
            "WIF-USD":  "dogwifhat — top Solana meme coin",
            "BONK-USD": "Bonk — Solana's community meme coin",
            # Other
            "LTC-USD":  "Litecoin — 'silver to Bitcoin's gold,' fast cheap payments",
            "BNB-USD":  "BNB — Binance exchange token and BNB Chain gas fee",
            "FIL-USD":  "Filecoin — decentralized file storage network",
        },
    },
}


def display_symbol(sym: str) -> str:
    """Strip -USD suffix for cleaner crypto display."""
    return sym.replace("-USD", "").replace("-USDT", "")


def is_crypto(sym: str) -> bool:
    return sym.endswith("-USD") or sym.endswith("-USDT")


def resolve_sector(symbol: str, stock_sectors: dict[str, str]) -> str:
    """Look up sector for a symbol: config override first, then catalog scan."""
    if symbol in stock_sectors:
        return stock_sectors[symbol]
    for sector, info in SECTOR_CATALOG.items():
        if symbol in info["stocks"]:
            return sector
    return "General"


def get_sector_color(sector: str) -> str:
    return SECTOR_COLORS.get(sector, "white")


def get_catalog_description(symbol: str) -> str:
    for info in SECTOR_CATALOG.values():
        if symbol in info["stocks"]:
            return info["stocks"][symbol]
    return ""


def all_catalog_symbols() -> list[str]:
    seen = set()
    result = []
    for info in SECTOR_CATALOG.values():
        for sym in info["stocks"]:
            if sym not in seen:
                seen.add(sym)
                result.append(sym)
    return result
