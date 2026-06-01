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
    "Cybersecurity":          "deep_pink2",
    "Fintech":                "medium_turquoise",
    "Commodities & Bonds":    "khaki3",
    "Asian Markets":          "red1",
    "European Markets":       "cornflower_blue",
    "Latin America":          "chartreuse3",
    "Nigerian Exchange (NGX)":"green3",
    "African Markets":        "dark_orange",
    "Dividend & Value":       "wheat1",
    "Commodities & Mining":   "light_goldenrod2",
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
            "CRWV": "CoreWeave — AI cloud GPU provider; first to deploy Nvidia Vera Rubin NVL72",
            "AI":   "C3.ai — enterprise AI software applications",
            "SOUN": "SoundHound — voice AI for automotive and restaurants",
            "BBAI": "BigBear.ai — defense and intelligence AI",
            "PATH": "UiPath — robotic process automation (RPA) and AI workflows",
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
            "SMCI":  "Super Micro Computer — AI server systems for data centers",
            "HPE":   "Hewlett Packard Enterprise — servers, storage, and hybrid cloud infrastructure",
            "NTAP":  "NetApp — enterprise data storage and cloud data management",
            "DDOG":  "Datadog — cloud observability and security monitoring",
            "RBLX":  "Roblox — metaverse gaming platform, 80M+ daily users",
            "RDDT":  "Reddit — social media platform and community data moat",
            "HIMS":  "Hims & Hers — telehealth and direct-to-consumer pharma",
            "NOW":   "ServiceNow — enterprise workflow automation and AI platform",
            "ANET":  "Arista Networks — cloud networking switches for AI data centers",
            "SNOW":  "Snowflake — cloud data platform and AI data sharing",
            "TTD":   "The Trade Desk — programmatic digital advertising platform",
            "APP":   "AppLovin — AI-powered mobile app growth and advertising",
            "MSTR":  "MicroStrategy — largest corporate Bitcoin holder + analytics BI",
            "DUOL":  "Duolingo — AI-powered language learning app, 97M daily users",
            "MNDY":  "Monday.com — AI-powered work management and project collaboration platform",
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
    "Cybersecurity": {
        "description": "Software and hardware companies protecting networks, endpoints, and cloud infrastructure.",
        "key_drivers": [
            "Enterprise security spend (growing even in downturns)",
            "Ransomware incidents and breach headlines",
            "Government regulation (NIS2, CMMC, SEC disclosure rules)",
            "Zero-trust and SASE architecture adoption",
            "AI-powered threat detection arms race",
        ],
        "stocks": {
            "CRWD": "CrowdStrike — endpoint protection leader, Falcon AI platform",
            "PANW": "Palo Alto Networks — network security, SASE, and SOC automation",
            "NET":  "Cloudflare — edge network security, DDoS protection, Zero Trust",
            "ZS":   "Zscaler — cloud-native zero trust network access (ZTNA)",
            "OKTA": "Okta — identity and access management (IAM) platform",
            "FTNT": "Fortinet — firewall appliances and Secure SD-WAN",
            "S":    "SentinelOne — AI-powered autonomous threat detection and response",
            "CYBR": "CyberArk — privileged access management and secrets security",
        },
    },
    "Healthcare & Biotech": {
        "description": "Drug makers, insurers, medical devices, and biotech companies.",
        "key_drivers": [
            "FDA approval/rejection decisions",
            "Drug pricing legislation",
            "Clinical trial results",
            "Healthcare utilization trends",
            "GLP-1 obesity drug growth trajectory",
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
            "ABT":  "Abbott Laboratories — diagnostics, medical devices, nutrition",
            "ISRG": "Intuitive Surgical — da Vinci robotic surgery systems",
            "MDT":  "Medtronic — cardiac devices, insulin pumps, surgical robotics",
            "BMY":  "Bristol-Myers Squibb — Opdivo/Eliquis blockbusters",
            "VRTX": "Vertex Pharmaceuticals — cystic fibrosis monopoly + gene-editing pipeline",
            "BIIB": "Biogen — Leqembi Alzheimer's drug and multiple sclerosis treatments",
            "ILMN": "Illumina — genomic DNA sequencing platforms and consumables",
            "DXCM": "Dexcom — continuous glucose monitors (CGM) for diabetes management",
            "GEHC": "GE HealthCare — medical imaging, ultrasound, and patient monitoring",
            "INCY": "Incyte — JAK inhibitor oncology drugs (Jakafi, Opzelura)",
            "BSX":  "Boston Scientific — cardiovascular, neuromodulation, and urology devices",
            "SYK":  "Stryker — orthopedic implants, Mako surgical robots, and med-surg equipment",
            "PODD": "Insulet — OmniPod tubeless insulin pump; largest addressable diabetes market",
            "REGN": "Regeneron — Dupixent (blockbuster biologic), Eylea, and oncology pipeline",
            "MRNA": "Moderna — mRNA platform; COVID vaccine + oncology and rare disease pipeline",
            "GILD": "Gilead Sciences — HIV antivirals (Biktarvy), oncology, and liver disease drugs",
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
            "DIA":  "SPDR Dow Jones Industrial Average ETF",
            "XLK":  "Technology Select Sector SPDR",
            "XLV":  "Healthcare Select Sector SPDR",
            "XLF":  "Financials Select Sector SPDR",
            "XLE":  "Energy Select Sector SPDR",
            "ARKK": "ARK Innovation — disruptive tech, high risk/reward",
            "SOXX": "iShares Semiconductor ETF",
            "BOTZ": "Global Robotics & AI ETF",
            "VWO":  "Vanguard FTSE Emerging Markets ETF — 5,000+ EM stocks (China, India, Brazil)",
            "KSA":  "iShares MSCI Saudi Arabia ETF — Saudi Aramco + Vision 2030 stocks",
            # Leveraged ETFs
            "SOXL": "Direxion 3x Semiconductor Bull — amplified SOXX exposure",
            "TQQQ": "ProShares 3x QQQ Bull — amplified Nasdaq-100 exposure",
            "UPRO": "ProShares 3x S&P 500 Bull — amplified SPY exposure",
            # Thematic ETFs
            "ICLN": "iShares Global Clean Energy ETF — solar, wind, hydro",
            "LIT":  "Global X Lithium & Battery Tech — EV supply chain",
            "DRIV": "Global X Autonomous & Electric Vehicles ETF",
            "SKYY": "First Trust Cloud Computing ETF — SaaS and IaaS leaders",
            "CLOU": "Global X Cloud Computing ETF — pure-play cloud companies",
            "AIQ":  "Global X AI & Technology ETF — AI hardware and software",
            "JETS": "US Global Jets ETF — airlines and airport operators",
            "XBI":  "SPDR S&P Biotech ETF — equal-weight biotech exposure",
            "HACK": "ETFMG Prime Cyber Security ETF — cybersecurity pure-plays",
        },
    },
    "Commodities & Bonds": {
        "description": "Gold, silver, oil, and bond ETFs — hedges against inflation and equity market volatility.",
        "key_drivers": [
            "US dollar strength (inverse relationship with gold/oil)",
            "Federal Reserve rate decisions (drives bond prices)",
            "Geopolitical tensions and supply disruptions",
            "Inflation expectations (CPI, PPI data)",
            "OPEC+ production quotas",
        ],
        "stocks": {
            "GLD":  "SPDR Gold Shares — largest gold ETF, tracks spot gold price",
            "SLV":  "iShares Silver Trust — tracks spot silver price",
            "GDX":  "VanEck Gold Miners ETF — basket of gold mining stocks",
            "USO":  "United States Oil Fund — tracks front-month WTI crude futures",
            "TLT":  "iShares 20+ Year Treasury Bond ETF — long-duration US government bonds",
            "HYG":  "iShares High Yield Corporate Bond ETF — 'junk bonds' barometer",
            "BNO":  "United States Brent Oil Fund — Brent crude futures",
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
            "C":     "Citigroup — global banking with large international footprint",
            "SCHW":  "Charles Schwab — retail brokerage and asset management",
            "PGR":   "Progressive — fastest-growing US auto insurer; usage-based Snapshot telematics",
            "CB":    "Chubb — world's largest publicly traded P&C insurer; commercial and specialty lines",
            "AFL":   "Aflac — supplemental insurance leader; 50%+ Japan market share",
            "MET":   "MetLife — global life insurance, annuities, and employee benefits",
        },
    },
    "Fintech": {
        "description": "Technology-driven financial services — payments, lending, crypto infrastructure, and neobanks.",
        "key_drivers": [
            "Consumer digital payment adoption",
            "Interest rate environment (affects BNPL and lending margins)",
            "Regulatory treatment of crypto and digital assets",
            "Banking charter access for neobanks",
            "Cross-border payment volumes",
        ],
        "stocks": {
            "PYPL": "PayPal — digital wallet and online payment network",
            "COIN": "Coinbase — largest US crypto exchange and custodian",
            "HOOD": "Robinhood — commission-free stock and crypto trading app",
            "SOFI": "SoFi Technologies — neobank: student loans, mortgages, investing",
            "AFRM": "Affirm — buy-now-pay-later (BNPL) for e-commerce",
            "UPST": "Upstart — AI-powered personal loan underwriting platform",
            "ADYEY":"Adyen — global payment processing for enterprise (Spotify, Netflix)",
            "NU":   "Nubank — Brazil/LatAm digital bank; 100M+ customers, most profitable neobank",
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
            "CEG":  "Constellation Energy — largest US nuclear fleet, powering AI data centers",
            "VST":  "Vistra Energy — nuclear + gas power generator, AI energy beneficiary",
            "NRG":  "NRG Energy — retail electricity and power generation",
            "CCJ":  "Cameco — world's largest publicly traded uranium producer",
            "LEU":  "Centrus Energy — domestic uranium enrichment for nuclear fuel",
            "ENPH": "Enphase Energy — residential solar microinverters",
            "FSLR": "First Solar — utility-scale thin-film solar panels",
            "PLUG": "Plug Power — hydrogen fuel cells and electrolyzers",
            "EQT":  "EQT Corp — largest US natural gas producer; Appalachian Basin operations",
            "AR":   "Antero Resources — natural gas and NGL producer; low-cost Appalachian assets",
            "FCEL": "FuelCell Energy — direct fuel cell power plants; clean hydrogen and baseload generation",
        },
    },
    "Consumer": {
        "description": "Retail, food, media, and brand companies exposed to consumer spending trends.",
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
            "DIS":  "Disney — streaming (D+), theme parks, and film studio",
            "ABNB": "Airbnb — global home-sharing and experiences marketplace",
            "DASH": "DoorDash — US restaurant delivery market leader",
            "KO":   "Coca-Cola — global beverage giant, 200+ countries",
            "PG":   "Procter & Gamble — household brands (Tide, Gillette, Pampers)",
            "SBUX": "Starbucks — global coffee chain with loyalty flywheel",
            "SPOT": "Spotify — global audio streaming leader, 600M+ users",
            "CELH": "Celsius Holdings — fastest-growing energy drink brand in the US",
            "MELI": "MercadoLibre — Latin America's e-commerce + fintech giant",
            "LULU": "Lululemon — premium athletic apparel; strong DTC and international growth",
            "TJX":  "TJX Companies — off-price retail (TJ Maxx, Marshalls); recession-resilient",
            "MNST": "Monster Beverage — #2 energy drink globally; high-margin royalty model with COKE",
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
            "NVTS": "Navitas Semiconductor — GaN and SiC power ICs for EV charging, solar, and AI PSUs",
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
            "NOC":  "Northrop Grumman — B-21 stealth bomber, space systems, and cyber defense",
            "GD":   "General Dynamics — Gulfstream jets, nuclear submarines, and land systems",
            "HII":  "Huntington Ingalls — sole builder of US Navy nuclear-powered aircraft carriers",
            "JOBY": "Joby Aviation — electric air taxi (eVTOL) for urban passenger flights",
            "ACHR": "Archer Aviation — eVTOL air taxi with United Airlines partnership",
            "MMM":  "3M — diversified industrial products and adhesives conglomerate",
            "CSX":  "CSX — major US freight railroad operator",
            "NOC":  "Northrop Grumman — B-21 stealth bomber, space and cyber defense",
            "LHX":  "L3Harris Technologies — defense electronics, ISR systems, and comms",
            "CACI": "CACI International — defense IT services and intelligence solutions",
            "LDOS": "Leidos — defense IT, health IT, and civil government services",
            "AXON": "Axon Enterprise — Tasers, body cameras, and cloud police software",
            "RKLB": "Rocket Lab USA — small satellite launch vehicles and spacecraft systems",
            "ASTS": "AST SpaceMobile — satellite-based direct-to-phone broadband network",
        },
    },
    "Latin America": {
        "description": "Leading Latin American equities and ETFs — Brazil's commodity and fintech giants, and the region's Amazon.",
        "key_drivers": [
            "Brazil SELIC interest rate and BRL exchange rate",
            "Iron ore and commodity prices (Vale, Petrobras)",
            "Emerging market risk-on/risk-off sentiment",
            "US dollar strength (inverse for EM assets)",
            "Political stability and fiscal policy in Brazil/Mexico",
        ],
        "stocks": {
            "MELI":  "MercadoLibre — Latin America's Amazon + Mercado Pago fintech",
            "VALE":  "Vale — world's largest iron ore and nickel miner (Brazil)",
            "ITUB":  "Itaú Unibanco — largest bank in Latin America",
            "EWZ":   "iShares MSCI Brazil ETF — broad Brazil large-cap exposure",
            "GLOB":  "Globant — LatAm IT services and digital transformation; Disney, Google clients",
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
            # Southeast Asia
            "SE":    "Sea Limited — Shopee e-commerce, Garena gaming, SeaMoney fintech (Singapore)",
            "GRAB":  "Grab Holdings — Southeast Asia super-app: ride-hail, food, fintech (8 countries)",
            # Regional ETFs
            "EWJ":   "iShares MSCI Japan ETF — broad Japan large-cap exposure",
            "MCHI":  "iShares MSCI China ETF — 600+ Chinese large/mid caps",
            "INDA":  "iShares MSCI India ETF — India's top 85% market-cap stocks",
            "EWY":   "iShares MSCI South Korea ETF — Samsung, SK Hynix, Hyundai",
            "FXI":   "iShares China Large-Cap ETF — 50 largest H-share Chinese stocks",
            "KWEB":  "KraneShares China Internet ETF — Alibaba, Tencent, Meituan, JD",
            "EWT":   "iShares MSCI Taiwan ETF — TSMC, MediaTek, Foxconn",
            "EWA":   "iShares MSCI Australia ETF — BHP, CSL, CBA, Macquarie",
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
            # Australia (dual-listed London/ASX)
            "BHP":   "BHP Group — world's largest mining company; iron ore, copper, coal",
            # Nordic / Denmark
            "NVO":   "Novo Nordisk — world's largest GLP-1 (Ozempic/Wegovy) maker, Denmark",
            # Italy
            "RACE":  "Ferrari — ultra-premium sports cars; near-zero demand elasticity",
            # Netherlands
            "STLA":  "Stellantis — Jeep, RAM, Peugeot, Citroën, Fiat parent (top-5 global auto)",
            "ING":   "ING Groep — pan-European retail and wholesale bank",
            # Switzerland / Italy chips
            "STM":   "STMicroelectronics — automotive & industrial chip leader (EU's top chip maker)",
            # Finland
            "NOK":   "Nokia — telecom infrastructure and 5G network equipment",
            # Regional ETFs
            "VGK":   "Vanguard FTSE Europe ETF — 1,300+ European stocks",
            "EZU":   "iShares MSCI Eurozone ETF — 18-country eurozone exposure",
            "EWU":   "iShares MSCI United Kingdom ETF — FTSE large/mid caps",
        },
    },
    "African Markets": {
        "description": "Leading African equities — South Africa's telecoms and media giants, listed as US ADRs.",
        "key_drivers": [
            "South African rand (ZAR) exchange rate",
            "Sub-Saharan Africa subscriber growth",
            "Tencent stake value (NPSNY holds ~25% of Tencent)",
            "African internet and mobile money penetration",
        ],
        "stocks": {
            "MTNOY": "MTN Group — Africa's largest telecom; 280M+ subscribers across 19 countries",
            "NPSNY": "Naspers/Prosus — South Africa tech holding company; major Tencent shareholder",
            "AAF.L": "Anglo African Finance — London-listed Nigerian financial services",
            "SEPL.L": "Seplat Energy — Nigerian oil & gas producer, London-listed",
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
            "DOT-USD":       "Polkadot — cross-chain interoperability protocol",
            "ATOM-USD":      "Cosmos — 'internet of blockchains' via IBC protocol",
            "NEAR-USD":      "NEAR Protocol — sharded L1 with AI + blockchain focus",
            "APT21794-USD":  "Aptos — Move language L1 from ex-Meta Diem engineers",
            "SUI20947-USD":  "Sui — object-centric Move L1, high throughput",
            "TON-USD":       "Toncoin — Telegram's blockchain, 900M+ user access",
            "HBAR-USD":      "Hedera — enterprise hashgraph, fast and energy-efficient",
            "XLM-USD":       "Stellar — cross-border payments, institutional focus",
            "ALGO-USD":      "Algorand — pure proof-of-stake, carbon-negative chain",
            "VET-USD":       "VeChain — supply chain and enterprise blockchain",
            "ICP-USD":       "Internet Computer — decentralized cloud compute (Dfinity)",
            # Layer 2s / DeFi
            "POL28321-USD":  "Polygon (POL) — Ethereum L2 and multi-chain scaling solution",
            "ARB-USD":       "Arbitrum — largest Ethereum L2 by total value locked",
            "OP-USD":        "Optimism — Ethereum L2 with Superchain multi-chain vision",
            "LINK-USD":      "Chainlink — oracle network connecting blockchains to real-world data",
            "UNI7083-USD":   "Uniswap — governance token of the largest DEX by volume",
            "AAVE-USD":      "Aave — leading decentralized lending and borrowing protocol",
            "MKR-USD":       "Maker — governs DAI stablecoin, oldest DeFi protocol",
            "LDO-USD":       "Lido DAO — liquid staking protocol; issues stETH for Ethereum stakers",
            "CRV-USD":       "Curve Finance — stablecoin AMM DEX optimised for low-slippage swaps",
            "GRT6719-USD":   "The Graph — indexing protocol ('Google for blockchains')",
            # AI / DePIN tokens
            "RENDER-USD":    "Render — decentralized GPU rendering network for AI and 3D",
            "FET-USD":       "Fetch.ai (ASI) — AI agents on blockchain, merged with Ocean+SingularityNET",
            "SEI-USD":       "Sei — high-performance L1 optimized for trading and DeFi",
            "TAO22974-USD":  "Bittensor — decentralized AI network with incentivised machine learning",
            # New ecosystems / RWA
            "TIA-USD":       "Celestia — modular blockchain providing a dedicated data availability layer",
            "WLD-USD":       "Worldcoin — iris-scan proof-of-personhood + global UBI token (Tools for Humanity)",
            "JUP-USD":       "Jupiter — leading Solana DEX aggregator and liquidity router",
            "ENA-USD":       "Ethena — synthetic dollar protocol (USDe) backed by ETH staking yield",
            "ONDO-USD":      "Ondo Finance — tokenised US Treasury RWA protocol for on-chain yield",
            "IMX10603-USD":  "Immutable X — Ethereum L2 for gaming and NFTs; gas-free minting",
            # Gaming / Metaverse
            "SAND-USD":      "The Sandbox — voxel metaverse with user-generated content and LAND NFTs",
            "MANA-USD":      "Decentraland — 3D virtual world with MANA governance and LAND parcels",
            "AXS-USD":       "Axie Infinity — play-to-earn NFT game; pioneered blockchain gaming",
            "CHZ-USD":       "Chiliz — fan token platform for sports clubs (Barca, PSG, Juventus)",
            # DeFi / cross-chain
            "INJ-USD":       "Injective — high-speed L1 for DeFi derivatives and orderbook DEXes",
            "RUNE-USD":      "THORchain — native cross-chain DEX; swap BTC/ETH/BNB without wrapping",
            "STX4847-USD":   "Stacks — Bitcoin L2 enabling smart contracts and DeFi on Bitcoin",
            # Privacy / PoW alts
            "ZEC-USD":       "Zcash — privacy coin using zk-SNARKs for shielded transactions",
            "KAS-USD":       "Kaspa — fastest PoW blockchain using GHOSTDAG; 10 blocks/second",
            # Meme coins
            "DOGE-USD":      "Dogecoin — original meme coin, Elon Musk favourite",
            "SHIB-USD":      "Shiba Inu — meme coin ecosystem with ShibaSwap DEX",
            "PEPE24478-USD": "Pepe — largest frog-themed meme coin by market cap",
            "WIF-USD":       "dogwifhat — top Solana meme coin",
            "BONK-USD":      "Bonk — Solana's community meme coin airdropped to NFT holders",
            "FLOKI-USD":     "Floki — meme coin with Valhalla gaming metaverse and DeFi ecosystem",
            # Other blue-chip alts
            "LTC-USD":       "Litecoin — 'silver to Bitcoin's gold,' fast cheap payments",
            "BNB-USD":       "BNB — Binance exchange token and BNB Chain gas fee",
            "FIL-USD":       "Filecoin — decentralized file storage network",
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
