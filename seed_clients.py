"""
seed_clients.py – Seed multiple demo clients with different portfolios.

Usage: python seed_clients.py
"""

from datetime import datetime, date, time

from models import (
    init_db,
    get_session_factory,
    Client,
    Account,
    Portfolio,
    Holding,
    Security,
    AccountTypeEnum,
    RelationshipManager,
    ClientPersonalDetails,
    Meeting,
    ClientMeetingSummary,
    SectorMaster,
    ClientPreference,
    ClientRiskOverview,
    SecurityPriceHistory,
    Transaction,
    ClientAITalkingPoints,
    FundList,
    Theme
)

from config.settings import DATABASE_URL


# ---------------- Relationship Managers -----------------------

RMS = [
    {"id": 1001, "rm_code": "RM001", "name": "John Smith"},
    {"id": 1002, "rm_code": "RM002", "name": "Sarah Lee"},
]

# ==============================================
# PREDEFINED INVESTMENT THEMES
# ==============================================

THEMES = [
    {
        "theme_code": "THM_001",
        "theme_name": "Artificial Intelligence, Automation & Advanced Computing",
        "category": "Technology & Innovation",
        "description": "Structural adoption and commercialization of artificial intelligence, machine learning, intelligent software, robotics, automation, semiconductors and advanced computing technologies across industries.",
        "classification_guidance": "Use when the primary investment narrative concerns AI adoption, generative AI, machine learning, AI agents, robotics, automation, autonomous systems, semiconductors, GPUs, AI accelerators or advanced computing."
    },
    {
        "theme_code": "THM_002",
        "theme_name": "Digital Infrastructure & Cloud",
        "category": "Technology & Innovation",
        "description": "Expansion of infrastructure supporting the digital economy, including cloud computing, data centers, networking, connectivity, telecom infrastructure and large-scale computing capacity.",
        "classification_guidance": "Use when the primary investment narrative concerns data centers, cloud infrastructure, hyperscaler capital expenditure, networking, telecom infrastructure, fiber connectivity, 5G or expansion of digital computing infrastructure."
    },
    {
        "theme_code": "THM_003",
        "theme_name": "Cybersecurity & Digital Trust",
        "category": "Technology & Innovation",
        "description": "Growing demand for cybersecurity, identity protection, privacy, data protection and resilient digital infrastructure as economic activity becomes increasingly digital.",
        "classification_guidance": "Use when the primary investment narrative concerns cybersecurity spending, cyber threats, data protection, cloud security, network security, identity management, digital trust or protection of critical digital infrastructure."
    },
    {
        "theme_code": "THM_004",
        "theme_name": "Digital Finance & Financial Innovation",
        "category": "Technology & Innovation",
        "description": "Transformation of financial services through digital payments, fintech, blockchain, tokenization, digital assets, embedded finance and next-generation financial infrastructure.",
        "classification_guidance": "Use when the primary investment narrative concerns technology-driven transformation of payments, banking, financial platforms, blockchain, digital assets, tokenization or other financial technology."
    },
    {
        "theme_code": "THM_005",
        "theme_name": "Energy Transition, Electrification & Power Infrastructure",
        "category": "Energy, Resources & Environment",
        "description": "Structural transformation of energy systems through renewable generation, electrification, energy storage, electric mobility and expansion or modernization of electricity and power infrastructure.",
        "classification_guidance": "Use when the primary investment narrative concerns renewable energy, electrification, batteries, electric vehicles, energy storage, power generation, grids, transmission infrastructure, utilities or rising electricity demand including demand related to AI and data centers."
    },
    {
        "theme_code": "THM_006",
        "theme_name": "Critical Resources & Natural Capital",
        "category": "Energy, Resources & Environment",
        "description": "Strategic demand and supply dynamics affecting critical minerals, metals, water, food systems and other natural resources essential to economic, technological and environmental development.",
        "classification_guidance": "Use when the primary investment narrative concerns critical minerals, strategic commodities, mining capacity, resource scarcity, water availability, agriculture, food security or sustainable management of natural resources."
    },
    {
        "theme_code": "THM_007",
        "theme_name": "Healthcare Innovation & Longevity",
        "category": "Healthcare & Demographics",
        "description": "Structural transformation of healthcare through biotechnology, innovative medicines, medical technology, diagnostics, digital health and increasing healthcare demand associated with ageing populations and longer lifespans.",
        "classification_guidance": "Use when the primary investment narrative concerns biotechnology, pharmaceutical innovation, next-generation treatments, medical devices, diagnostics, digital health, ageing populations, longevity or increasing age-related healthcare demand."
    },
    {
        "theme_code": "THM_008",
        "theme_name": "Demographic & Consumer Transformation",
        "category": "Demographics & Society",
        "description": "Structural changes in population, household behavior, workforce composition and consumption patterns driven by demographic evolution, income growth, digital lifestyles and changing consumer preferences.",
        "classification_guidance": "Use when the primary investment narrative concerns demographic change, changing consumer behavior, emerging-market consumption, digital commerce, lifestyle transformation, workforce demographics or structural changes in household spending."
    },
    {
        "theme_code": "THM_009",
        "theme_name": "Geopolitical Fragmentation, Defense & Security",
        "category": "Geopolitics & Security",
        "description": "Investment implications of increasing geopolitical competition, economic fragmentation, trade restrictions, defense spending and national-security priorities in a more multipolar global economy.",
        "classification_guidance": "Use when the primary investment narrative concerns geopolitical competition, trade wars, tariffs, sanctions, export controls, defense spending, military modernization, aerospace security or strategic national-security priorities."
    },
    {
        "theme_code": "THM_010",
        "theme_name": "Supply Chain Resilience & Reshoring",
        "category": "Geopolitics & Industrial Transformation",
        "description": "Restructuring of global supply chains toward greater resilience, diversification, localization, reshoring, nearshoring and reduced dependence on strategically vulnerable suppliers and regions.",
        "classification_guidance": "Use when the primary investment narrative concerns manufacturing relocation, reshoring, nearshoring, friend-shoring, supplier diversification, localization of production or strategic restructuring of global supply chains."
    },
    {
        "theme_code": "THM_011",
        "theme_name": "Industrial Modernization & Infrastructure",
        "category": "Industrial Transformation",
        "description": "Long-term investment in manufacturing capacity, industrial modernization, physical infrastructure, transportation systems and productivity-enhancing industrial technologies.",
        "classification_guidance": "Use when the primary investment narrative concerns reindustrialization, manufacturing investment, factory construction, industrial capital expenditure, transportation infrastructure, industrial equipment or modernization of physical production systems."
    },
    {
        "theme_code": "THM_012",
        "theme_name": "Monetary Policy & Interest Rate Cycle",
        "category": "Macro & Capital Markets",
        "description": "Market implications of central-bank policy, interest-rate cycles, liquidity, financial conditions and transitions between monetary tightening, easing and normalization regimes.",
        "classification_guidance": "Use when the primary investment narrative concerns central-bank decisions, interest-rate increases or cuts, monetary tightening or easing, yield-curve changes, liquidity conditions or monetary-policy divergence."
    },
    {
        "theme_code": "THM_013",
        "theme_name": "Inflation & Cost Pressures",
        "category": "Macro & Capital Markets",
        "description": "Investment implications of persistent, accelerating or declining inflation across wages, commodities, energy, goods, services and corporate input costs.",
        "classification_guidance": "Use when the primary investment narrative concerns inflation, disinflation, wage pressures, commodity-driven inflation, energy prices, input costs, pricing pressure or corporate pricing power."
    },
    {
        "theme_code": "THM_014",
        "theme_name": "Fiscal Policy & Government Investment",
        "category": "Macro & Capital Markets",
        "description": "Market effects of government spending, fiscal stimulus, taxation, deficits, sovereign debt, subsidies, infrastructure programs and strategic industrial policy.",
        "classification_guidance": "Use when the primary investment narrative concerns fiscal policy, public spending, sovereign borrowing, taxation, government subsidies, fiscal stimulus, infrastructure programs or government-led strategic investment."
    },
    {
        "theme_code": "THM_015",
        "theme_name": "Capital Markets, M&A & Corporate Restructuring",
        "category": "Macro & Capital Markets",
        "description": "Market developments resulting from mergers, acquisitions, IPOs, private capital activity, corporate consolidation, restructuring, spin-offs and changing corporate capital-allocation activity.",
        "classification_guidance": "Use when the primary investment narrative concerns mergers and acquisitions, corporate consolidation, IPO activity, private equity transactions, spin-offs, restructuring, takeovers or major strategic asset transactions."
    },
]

# ---------------- SectorMasters -------------------------------
sector_master = [

    {
        "id": 1,
        "name": "Technology",
        "gics_code": "45",
        "description": "Software, cloud computing and enterprise technology companies"
    },

    {
        "id": 2,
        "name": "Semiconductors",
        "gics_code": "45301",
        "description": "Chip manufacturing and semiconductor equipment companies"
    },

    {
        "id": 3,
        "name": "Financials",
        "gics_code": "40",
        "description": "Banking, fixed income instruments and financial services"
    },

    {
        "id": 4,
        "name": "Energy",
        "gics_code": "10",
        "description": "Traditional energy sector including oil and gas"
    },

    {
        "id": 5,
        "name": "Healthcare",
        "gics_code": "35",
        "description": "Healthcare and pharmaceutical companies"
    },

    {
        "id": 6,
        "name": "Consumer Discretionary",
        "gics_code": "25",
        "description": "Consumer products and retail companies"
    },

    {
        "id": 9,
        "name": "Real Estate",
        "gics_code": "60",
        "description": "Real estate investment trusts and property funds"
    },

    {
        "id": 12,
        "name": "Renewable Energy",
        "gics_code": "10RE",
        "description": "ESG focused green and renewable energy investments"
    },

    {
        "id": 13,
        "name": "Industrials",
        "gics_code": "20",
        "description": "Industrial manufacturing, automation and infrastructure companies"
    },

    {
        "id": 14,
        "name": "Communication Services",
        "gics_code": "50",
        "description": "Telecom, media and internet platform companies"
    },

    {
        "id": 15,
        "name": "Materials",
        "gics_code": "15",
        "description": "Mining, metals and commodity producers"
    },

    {
        "id": 16,
        "name": "Utilities",
        "gics_code": "55",
        "description": "Electricity, water and regulated utility companies"
    },

    {
        "id": 17,
        "name": "E-Commerce",
        "gics_code": "2550",
        "description": "Online retail and digital commerce companies"
    },

    {
        "id": 23,
        "name": "Small Cap",
        "gics_code": "4520",
        "description": "Small-cap companies with high growth potential"
    },

    {
        "id": 24,
        "name": "Artificial Intelligence",
        "gics_code": "4511",
        "description": "Artificial intelligence, machine learning and AI software companies"
    },

    {
        "id": 25,
        "name": "Cloud Computing",
        "gics_code": "4512",
        "description": "Cloud infrastructure, SaaS and cloud platform providers"
    },

    {
        "id": 20,
        "name": "Digital Infrastructure",
        "gics_code": "4513",
        "description": "Data centers, networking, compute infrastructure and digital connectivity"
    },

    {
        "id": 21,
        "name": "Cybersecurity",
        "gics_code": "4514",
        "description": "Cybersecurity, identity protection and network security companies"
    },

    {
        "id": 22,
        "name": "Blockchain",
        "gics_code": "4515",
        "description": "Blockchain technology, distributed ledger and digital asset ecosystem"
    },



    {
        "id": 18,
        "name": "Cryptocurrency",
        "gics_code": "4510",
        "description": "Blockchain and digital asset ecosystem"
    }

]

# ---------------- Fund List -----------------------------------

FUNDS = [

    # Technology
    {
        "fund_id": "F001",
        "fund_name": "Global Technology Leaders Fund",
        "risk": "Moderate",
        "sector": "Technology",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F002",
        "fund_name": "Digital Innovation Fund",
        "risk": "Aggressive",
        "sector": "Technology",
        "investment_style": "Growth"
    },

    # Semiconductors
    {
        "fund_id": "F003",
        "fund_name": "Global Semiconductor Growth Fund",
        "risk": "Aggressive",
        "sector": "Semiconductors",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F004",
        "fund_name": "AI Infrastructure Leaders Fund",
        "risk": "Moderate",
        "sector": "Semiconductors",
        "investment_style": "Growth"
    },

    # Financials
    {
        "fund_id": "F005",
        "fund_name": "European Financial Opportunities Fund",
        "risk": "Moderate",
        "sector": "Financials",
        "investment_style": "Balanced"
    },
    {
        "fund_id": "F006",
        "fund_name": "Dividend Income Fund",
        "risk": "Conservative",
        "sector": "Financials",
        "investment_style": "Income"
    },

    # Healthcare
    {
        "fund_id": "F007",
        "fund_name": "Global Healthcare Leaders Fund",
        "risk": "Moderate",
        "sector": "Healthcare",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F0202",
        "fund_name": "Healthcare Opportunities ESG Fund",
        "risk": "Moderate",
        "sector": "Healthcare",
        "investment_style": "Balanced"
    },
    {
        "fund_id": "F0230",
        "fund_name": "Global Life Sciences Growth Fund",
        "risk": "Aggressive",
        "sector": "Healthcare",
        "investment_style": "Growth"
    },

    # Renewable Energy
    {
        "fund_id": "F008",
        "fund_name": "Clean Energy Growth Fund",
        "risk": "Aggressive",
        "sector": "Renewable Energy",
        "investment_style": "Growth"
    },

    # Consumer Discretionary
    {
        "fund_id": "F013",
        "fund_name": "Global Consumer Growth Fund",
        "risk": "Moderate",
        "sector": "Consumer Discretionary",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F014",
        "fund_name": "Consumer Lifestyle Opportunities Fund",
        "risk": "Aggressive",
        "sector": "Consumer Discretionary",
        "investment_style": "Growth"
    },

    # Energy
    {
        "fund_id": "F009",
        "fund_name": "Global Energy Opportunities Fund",
        "risk": "Moderate",
        "sector": "Energy",
        "investment_style": "Balanced"
    },

    # Real Estate
    {
        "fund_id": "F010",
        "fund_name": "European Real Estate Income Fund",
        "risk": "Conservative",
        "sector": "Real Estate",
        "investment_style": "Income"
    },

    # Industrials
    {
        "fund_id": "F015",
        "fund_name": "Global Industrials Leaders Fund",
        "risk": "Moderate",
        "sector": "Industrials",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F016",
        "fund_name": "Infrastructure Opportunities Fund",
        "risk": "Moderate",
        "sector": "Industrials",
        "investment_style": "Balanced"
    },
    {
        "fund_id": "F017",
        "fund_name": "Smart Manufacturing Growth Fund",
        "risk": "Aggressive",
        "sector": "Industrials",
        "investment_style": "Growth"
    },

    # Communication Services
    {
        "fund_id": "F018",
        "fund_name": "Global Communication Leaders Fund",
        "risk": "Moderate",
        "sector": "Communication Services",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F019",
        "fund_name": "Digital Media Opportunities Fund",
        "risk": "Aggressive",
        "sector": "Communication Services",
        "investment_style": "Growth"
    },

    # Materials
    {
        "fund_id": "F020",
        "fund_name": "Global Materials Leaders Fund",
        "risk": "Moderate",
        "sector": "Materials",
        "investment_style": "Balanced"
    },
    {
        "fund_id": "F021",
        "fund_name": "Commodity Growth Fund",
        "risk": "Aggressive",
        "sector": "Materials",
        "investment_style": "Growth"
    },

    # Utilities
    {
        "fund_id": "F022",
        "fund_name": "Global Utilities Income Fund",
        "risk": "Conservative",
        "sector": "Utilities",
        "investment_style": "Income"
    },
    {
        "fund_id": "F023",
        "fund_name": "Essential Infrastructure Fund",
        "risk": "Moderate",
        "sector": "Utilities",
        "investment_style": "Balanced"
    },

    # E-Commerce
    {
        "fund_id": "F024",
        "fund_name": "Global E-Commerce Growth Fund",
        "risk": "Moderate",
        "sector": "E-Commerce",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F025",
        "fund_name": "Digital Commerce Innovation Fund",
        "risk": "Aggressive",
        "sector": "E-Commerce",
        "investment_style": "Growth"
    },

    # Small Cap
    {
        "fund_id": "F028",
        "fund_name": "Global Small Cap Growth Fund",
        "risk": "Aggressive",
        "sector": "Small Cap",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F029",
        "fund_name": "Emerging Companies Fund",
        "risk": "Moderate",
        "sector": "Small Cap",
        "investment_style": "Growth"
    },

    # Artificial Intelligence
    {
        "fund_id": "F030",
        "fund_name": "AI Innovation Fund",
        "risk": "Aggressive",
        "sector": "Artificial Intelligence",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F031",
        "fund_name": "Global AI Leaders Fund",
        "risk": "Moderate",
        "sector": "Artificial Intelligence",
        "investment_style": "Growth"
    },

    # Cloud Computing
    {
        "fund_id": "F032",
        "fund_name": "Cloud Infrastructure Fund",
        "risk": "Moderate",
        "sector": "Cloud Computing",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F033",
        "fund_name": "Global Cloud Leaders Fund",
        "risk": "Aggressive",
        "sector": "Cloud Computing",
        "investment_style": "Growth"
    },

    # Cryptocurrency
    {
        "fund_id": "F026",
        "fund_name": "Digital Assets Strategy Fund",
        "risk": "Aggressive",
        "sector": "Cryptocurrency",
        "investment_style": "Growth"
    },
    {
        "fund_id": "F027",
        "fund_name": "Blockchain Innovation Fund",
        "risk": "Aggressive",
        "sector": "Cryptocurrency",
        "investment_style": "Growth"
    }
]


# ---------------- Securities ----------------
securities = [

    {
        "ticker": "ASML",
        "name": "ASML Holding",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 2,
        "currency": "EUR",
        "last_price": 850.0
    },

    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 2,
        "currency": "EUR",
        "last_price": 900.0
    },

    {
        "ticker": "MSFT",
        "name": "Microsoft Corporation",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 1,
        "currency": "EUR",
        "last_price": 430.0
    },

    {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 1,
        "currency": "EUR",
        "last_price": 195.0
    },

    {
        "ticker": "BOND1",
        "name": "Euro Gov Bond Fund",
        "security_type": "FIXED_INCOME",
        "exchange": "LSE",
        "sector_id": 3,
        "currency": "EUR",
        "last_price": 98.5
    },

    {
        "ticker": "BOND2",
        "name": "Short Duration Green Bond",
        "security_type": "FIXED_INCOME",
        "exchange": "LSE",
        "sector_id": 3,
        "currency": "EUR",
        "last_price": 95.0
    },

    {
        "ticker": "REIT1",
        "name": "European Real Estate ETF",
        "security_type": "REAL_ESTATE",
        "exchange": "EURONEXT",
        "sector_id": 9,
        "currency": "EUR",
        "last_price": 45.0
    },

    {
        "ticker": "ALT1",
        "name": "ESG Small Cap Fund",
        "security_type": "ALTERNATIVES",
        "exchange": "EURONEXT",
        "sector_id": 12,
        "currency": "EUR",
        "last_price": 62.0
    },

    {
        "ticker": "ALT2",
        "name": "Nordea Climate Fund",
        "security_type": "ALTERNATIVES",
        "exchange": "EURONEXT",
        "sector_id": 12,
        "currency": "EUR",
        "last_price": 58.0
    },

    {
        "ticker": "LIQ1",
        "name": "Money Market Fund",
        "security_type": "LIQUIDITY",
        "exchange": "EURONEXT",
        "sector_id": 3,
        "currency": "EUR",
        "last_price": 1.0
    },

    # Industrials
    {
        "ticker": "CAT",
        "name": "Caterpillar Inc.",
        "security_type": "EQUITY",
        "exchange": "NYSE",
        "sector_id": 13,
        "currency": "EUR",
        "last_price": 340.0
    },

    {
        "ticker": "SIEM",
        "name": "Siemens AG",
        "security_type": "EQUITY",
        "exchange": "XETRA",
        "sector_id": 13,
        "currency": "EUR",
        "last_price": 195.0
    },

    # Communication Services
    {
        "ticker": "META",
        "name": "Meta Platforms",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 14,
        "currency": "EUR",
        "last_price": 540.0
    },

    {
        "ticker": "GOOG",
        "name": "Alphabet Inc.",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 14,
        "currency": "EUR",
        "last_price": 185.0
    },

    # Materials
    {
        "ticker": "RIO",
        "name": "Rio Tinto plc",
        "security_type": "EQUITY",
        "exchange": "LSE",
        "sector_id": 15,
        "currency": "EUR",
        "last_price": 68.0
    },

    {
        "ticker": "BHP",
        "name": "BHP Group",
        "security_type": "EQUITY",
        "exchange": "LSE",
        "sector_id": 15,
        "currency": "EUR",
        "last_price": 45.0
    },

    # Utilities
    {
        "ticker": "NEE",
        "name": "NextEra Energy",
        "security_type": "EQUITY",
        "exchange": "NYSE",
        "sector_id": 16,
        "currency": "EUR",
        "last_price": 81.0
    },

    {
        "ticker": "ENEL",
        "name": "Enel S.p.A.",
        "security_type": "EQUITY",
        "exchange": "MIL",
        "sector_id": 16,
        "currency": "EUR",
        "last_price": 7.5
    },

    # E-Commerce
    {
        "ticker": "AMZN",
        "name": "Amazon.com Inc.",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 17,
        "currency": "EUR",
        "last_price": 210.0
    },

    {
        "ticker": "SHOP",
        "name": "Shopify Inc.",
        "security_type": "EQUITY",
        "exchange": "NYSE",
        "sector_id": 17,
        "currency": "EUR",
        "last_price": 92.0
    },

    # Cryptocurrency
    {
        "ticker": "COIN",
        "name": "Coinbase Global",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 18,
        "currency": "EUR",
        "last_price": 290.0
    },

    {
        "ticker": "MSTR",
        "name": "Strategy Inc.",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 18,
        "currency": "EUR",
        "last_price": 390.0
    }
]


security_price_history = [

    # ASML
    ("ASML","Feb",2026,780),
    ("ASML","Mar",2026,800),
    ("ASML","Apr",2026,785),
    ("ASML","May",2026,815),
    ("ASML","Jun",2026,805),
    ("ASML","Jul",2026,850),
    ("ASML","Aug",2026,None),
    ("ASML","Sep",2026,None),
    ("ASML","Oct",2026,None),
    ("ASML","Nov",2026,None),
    ("ASML","Dec",2026,None),
    ("ASML","Jan",2027,None),
    ("ASML","Feb",2027,None),

    # NVDA
    ("NVDA","Feb",2026,810),
    ("NVDA","Mar",2026,840),
    ("NVDA","Apr",2026,825),
    ("NVDA","May",2026,870),
    ("NVDA","Jun",2026,860),
    ("NVDA","Jul",2026,900),
    ("NVDA","Aug",2026,None),
    ("NVDA","Sep",2026,None),
    ("NVDA","Oct",2026,None),
    ("NVDA","Nov",2026,None),
    ("NVDA","Dec",2026,None),
    ("NVDA","Jan",2027,None),
    ("NVDA","Feb",2027,None),

    # MSFT
    ("MSFT","Feb",2026,390),
    ("MSFT","Mar",2026,400),
    ("MSFT","Apr",2026,395),
    ("MSFT","May",2026,418),
    ("MSFT","Jun",2026,412),
    ("MSFT","Jul",2026,430),
    ("MSFT","Aug",2026,None),
    ("MSFT","Sep",2026,None),
    ("MSFT","Oct",2026,None),
    ("MSFT","Nov",2026,None),
    ("MSFT","Dec",2026,None),
    ("MSFT","Jan",2027,None),
    ("MSFT","Feb",2027,None),

    # AAPL
    ("AAPL","Feb",2026,170),
    ("AAPL","Mar",2026,178),
    ("AAPL","Apr",2026,174),
    ("AAPL","May",2026,189),
    ("AAPL","Jun",2026,185),
    ("AAPL","Jul",2026,195),
    ("AAPL","Aug",2026,None),
    ("AAPL","Sep",2026,None),
    ("AAPL","Oct",2026,None),
    ("AAPL","Nov",2026,None),
    ("AAPL","Dec",2026,None),
    ("AAPL","Jan",2027,None),
    ("AAPL","Feb",2027,None),

    # BOND1
    ("BOND1","Feb",2026,94.0),
    ("BOND1","Mar",2026,95.2),
    ("BOND1","Apr",2026,94.8),
    ("BOND1","May",2026,96.8),
    ("BOND1","Jun",2026,97.4),
    ("BOND1","Jul",2026,98.5),
    ("BOND1","Aug",2026,None),
    ("BOND1","Sep",2026,None),
    ("BOND1","Oct",2026,None),
    ("BOND1","Nov",2026,None),
    ("BOND1","Dec",2026,None),
    ("BOND1","Jan",2027,None),
    ("BOND1","Feb",2027,None),

    # BOND2
    ("BOND2","Feb",2026,89.0),
    ("BOND2","Mar",2026,90.5),
    ("BOND2","Apr",2026,89.9),
    ("BOND2","May",2026,92.3),
    ("BOND2","Jun",2026,93.6),
    ("BOND2","Jul",2026,95.0),
    ("BOND2","Aug",2026,None),
    ("BOND2","Sep",2026,None),
    ("BOND2","Oct",2026,None),
    ("BOND2","Nov",2026,None),
    ("BOND2","Dec",2026,None),
    ("BOND2","Jan",2027,None),
    ("BOND2","Feb",2027,None),

    # REIT1
    ("REIT1","Feb",2026,39.0),
    ("REIT1","Mar",2026,41.0),
    ("REIT1","Apr",2026,40.2),
    ("REIT1","May",2026,43.1),
    ("REIT1","Jun",2026,42.5),
    ("REIT1","Jul",2026,45.0),
    ("REIT1","Aug",2026,None),
    ("REIT1","Sep",2026,None),
    ("REIT1","Oct",2026,None),
    ("REIT1","Nov",2026,None),
    ("REIT1","Dec",2026,None),
    ("REIT1","Jan",2027,None),
    ("REIT1","Feb",2027,None),

    # ALT1
    ("ALT1","Feb",2026,57.0),
    ("ALT1","Mar",2026,60.0),
    ("ALT1","Apr",2026,58.4),
    ("ALT1","May",2026,61.0),
    ("ALT1","Jun",2026,60.2),
    ("ALT1","Jul",2026,62.0),
    ("ALT1","Aug",2026,None),
    ("ALT1","Sep",2026,None),
    ("ALT1","Oct",2026,None),
    ("ALT1","Nov",2026,None),
    ("ALT1","Dec",2026,None),
    ("ALT1","Jan",2027,None),
    ("ALT1","Feb",2027,None),

    # ALT2
    ("ALT2","Feb",2026,51.0),
    ("ALT2","Mar",2026,53.0),
    ("ALT2","Apr",2026,52.0),
    ("ALT2","May",2026,55.3),
    ("ALT2","Jun",2026,54.5),
    ("ALT2","Jul",2026,58.0),
    ("ALT2","Aug",2026,None),
    ("ALT2","Sep",2026,None),
    ("ALT2","Oct",2026,None),
    ("ALT2","Nov",2026,None),
    ("ALT2","Dec",2026,None),
    ("ALT2","Jan",2027,None),
    ("ALT2","Feb",2027,None),

    # LIQ1
    ("LIQ1","Feb",2026,1.0),
    ("LIQ1","Mar",2026,1.0),
    ("LIQ1","Apr",2026,1.0),
    ("LIQ1","May",2026,1.0),
    ("LIQ1","Jun",2026,1.0),
    ("LIQ1","Jul",2026,1.0),
    ("LIQ1","Aug",2026,None),
    ("LIQ1","Sep",2026,None),
    ("LIQ1","Oct",2026,None),
    ("LIQ1","Nov",2026,None),
    ("LIQ1","Dec",2026,None),
    ("LIQ1","Jan",2027,None),
    ("LIQ1","Feb",2027,None),
]

# ---------------- Transactions ----------------

transactions = [

    {
        "account_id": 1,
        "transaction_type": "BUY",
        "ticker": "ASML",
        "product_name": "ASML Holding",
        "amount": 85000,
        "currency": "EUR",
        "transaction_date": "2026-06-25"
    },

    {
        "account_id": 1,
        "transaction_type": "BUY",
        "ticker": "ALT1",
        "product_name": "ESG Small Cap Fund",
        "amount": 120000,
        "currency": "EUR",
        "transaction_date": "2026-06-27"
    },

    {
        "account_id": 1,
        "transaction_type": "BUY",
        "ticker": "NVDA",
        "product_name": "NVIDIA Corporation",
        "amount": 150000,
        "currency": "EUR",
        "transaction_date": "2026-06-29"
    },

    {
        "account_id": 1,
        "transaction_type": "SELL",
        "ticker": "BOND2",
        "product_name": "Short Duration Green Bond",
        "amount": 90000,
        "currency": "EUR",
        "transaction_date": "2026-07-01"
    },

    {
        "account_id": 1,
        "transaction_type": "BUY",
        "ticker": "REIT1",
        "product_name": "European Real Estate ETF",
        "amount": 100000,
        "currency": "EUR",
        "transaction_date": "2026-07-02"
    },

    {
        "account_id": 2,
        "transaction_type": "BUY",
        "ticker": "BOND1",
        "product_name": "Euro Gov Bond Fund",
        "amount": 150000,
        "currency": "EUR",
        "transaction_date": "2026-06-18"
    },

    {
        "account_id": 2,
        "transaction_type": "BUY",
        "ticker": "REIT1",
        "product_name": "European Real Estate ETF",
        "amount": 80000,
        "currency": "EUR",
        "transaction_date": "2026-06-21"
    },

    {
        "account_id": 2,
        "transaction_type": "SELL",
        "ticker": "MSFT",
        "product_name": "Microsoft Corporation",
        "amount": 110000,
        "currency": "EUR",
        "transaction_date": "2026-06-24"
    },

    {
        "account_id": 2,
        "transaction_type": "BUY",
        "ticker": "BOND2",
        "product_name": "Short Duration Green Bond",
        "amount": 100000,
        "currency": "EUR",
        "transaction_date": "2026-06-28"
    },

    {
        "account_id": 2,
        "transaction_type": "BUY",
        "ticker": "LIQ1",
        "product_name": "Money Market Fund",
        "amount": 50000,
        "currency": "EUR",
        "transaction_date": "2026-07-01"
    },

    {
        "account_id": 3,
        "transaction_type": "BUY",
        "ticker": "BOND1",
        "product_name": "Euro Gov Bond Fund",
        "amount": 125000,
        "currency": "EUR",
        "transaction_date": "2026-06-15"
    },
    {
        "account_id": 3,
        "transaction_type": "BUY",
        "ticker": "AAPL",
        "product_name": "Apple Inc.",
        "amount": 95000,
        "currency": "EUR",
        "transaction_date": "2026-06-19"
    },
    {
        "account_id": 3,
        "transaction_type": "SELL",
        "ticker": "NVDA",
        "product_name": "NVIDIA Corporation",
        "amount": 85000,
        "currency": "EUR",
        "transaction_date": "2026-06-23"
    },

    {
        "account_id": 3,
        "transaction_type": "BUY",
        "ticker": "REIT1",
        "product_name": "European Real Estate ETF",
        "amount": 70000,
        "currency": "EUR",
        "transaction_date": "2026-06-26"
    },

    {
        "account_id": 3,
        "transaction_type": "BUY",
        "ticker": "LIQ1",
        "product_name": "Money Market Fund",
        "amount": 40000,
        "currency": "EUR",
        "transaction_date": "2026-06-30"
    }
]

# ---------------- Clients ----------------

CLIENTS = [
    {
        "code": "AB345678",
        "name": "Arjun Mehta",
        "risk": "Aggressive",
        "strategy": "Growth",
        "rm_id": 1001,
        "age":50,
        "phone":"+91-9923456789",
        "profession":"Entrepreneur (TECH)",
        "preference":"ESG Leader",
        "service_model":"Advisory - Active Advice",
        "investment_goals":"Wealth Growth, Sustainable Impact",

        "personal_details": {
            "marital_status": "Married",
            "kids_details": "2 children",
            "date_of_Birth": "1975-04-10",
            "hobbies": "Golf, Travel",
            "other": "Prefers face-to-face meetings",
            "client_constraints": "Maintain ESG focus,Limit single stock exposure below 35%,Avoid crypto investments,Prefer long-term growth opportunities"
        },

        "meeting": {
            "title": "Mr",
            "location": "Amsterdam - Zuid office",
            "platform": "In-person"
        },

#         "meeting_summary": {
#             "discussion_points": [
#                   "Client's business performed well in H2 2025 with strong revenue growth.",
#                   "Client accumulated €800K cash from dividends and business income and wanted to deploy it.",
#                   "Preference to increase sustainable European equity exposure, especially technology and green energy.",
#                   "Discussed impact of ECB rate trajectory on bond allocation.",
#                   "Agreed that RM would prepare specific ESG small-cap options for the next meeting."
#             ],
#             "questions": [
#                         "What is the outlook for European sustainable tech?",
#                         "Should I reduce my bond allocation given the rate environment?"
#             ]
#         },

        "holdings": [

            ("ASML",3500,780,850),
            ("NVDA",2500,820,900),
            ("MSFT",3000,390,430),
            ("BOND1",18000,95,98.5),
            ("REIT1",22000,40,45),
            ("ALT1",15000,55,62),
            ("ALT2",12000,52,58),
            ("LIQ1",300000,1,1)

        ],

        "preferences":[
            ("EQUITY",45,65),
            ("FIXED_INCOME",15,30),
            ("REAL_ESTATE",5,10),
            ("ALTERNATIVES",10,20),
            ("LIQUIDITY",2,8)
        ],

        "risk_overview":{
            "concentration_pct":"18",
            "concentration_asset":"NVDA",
            "sharpe_ratio":"1.5",
            "value_at_risk":"520",
            "max_drawdown":"7.1"
        }
    },
    {
        "code":"CD901234",
        "name":"Priya Sharma",
        "risk":"Conservative",
        "strategy":"Income",
        "rm_id":1001,
        "age":40,
        "phone":"+91-9812345678",
        "profession":"AI Engineer",
        "preference":"Standard",
        "service_model":"Advisory - Active Advice",
        "investment_goals":"Wealth Growth",

        "personal_details":{
            "marital_status":"Single",
            "kids_details":"None",
            "date_of_Birth":"1985-07-15",
            "hobbies":"Reading",
            "other":"Interested in AI sector",
            "client_constraints":"Low risk investments only,Minimum 25% allocation to fixed income,Avoid high volatility sectors,Prefer dividend generating assets,Long-term investments only"
        },

        "meeting":{
            "title":"Ms",
            "location":"Microsoft Teams",
            "platform":"Video Call"
        },

#         "meeting_summary":{
#             "discussion_points":["Client focused on stable income investments.",
#                                  "Discussed dividend-paying healthcare and banking stocks.",
#                                  "Reviewed current bond allocation strategy.",
#                                  "Explored tax-efficient portfolio options."],
#             "questions":[
#                          "Should I add healthcare exposure?",
#                          "What is the expected dividend outlook next year?"]
#         },

        "holdings":[

            ("AAPL",18000,170,195),
            ("BOND1",18000,94,98.5),
            ("BOND2",8000,90,95),
            ("REIT1",12000,42,45),
            ("ALT1",5000,55,62),
            ("LIQ1",500000,1,1)
        ],

        "preferences":[
            ("EQUITY",20,35),
            ("FIXED_INCOME",40,55),
            ("REAL_ESTATE",5,15),
            ("ALTERNATIVES",2,8),
            ("LIQUIDITY",5,12)
        ],

        "risk_overview":{
            "concentration_pct":"24",
            "concentration_asset":"BOND1",
            "sharpe_ratio":"1.2",
            "value_at_risk":"310",
            "max_drawdown":"4.9"
        }
    },

    {
        "code":"EF567890",
        "name":"Rahul Gupta",
        "risk":"Moderate",
        "strategy":"Balanced",
        "rm_id":1002,
        "age":60,
        "phone":"+91-9876543210",
        "profession":"Retired Industrialist",
        "preference":"No specific preference",
        "service_model":"Discretionary - Conservative",
        "investment_goals":"Capital Preservation, Income Generation",

        "personal_details":{
            "marital_status":"Married",
            "kids_details":"1 child",
            "date_of_Birth":"1965-09-08",
            "hobbies":"Tennis",
            "other":"Interested in AI",
            "client_constraints":"Capital preservation priority,Minimum 30% allocation to fixed income,Prefer dividend-paying assets,Avoid speculative investments,Maintain moderate portfolio volatility"
        },

        "meeting":{
            "title":"Mr",
            "location":"Amsterdam - Zuid office",
            "platform":"In person"
        },

#         "meeting_summary":{
#             "discussion_points":[ "Reviewed retirement income sustainability.",
#                                    "Discussed balancing equity exposure with fixed income holdings.",
#                                    "Evaluated dividend strategies for stable cash flow.",
#                                    "Reviewed succession and estate planning considerations.",
#                                    "RM to provide tax-efficient income strategies."],
#             "questions":["Can I improve portfolio income without increasing risk?",
#                          "Should I increase fixed income exposure?"]
#         },

        "holdings":[
                ("MSFT",1200,390,430),
                ("AAPL",1800,170,195),
                ("BOND1",15000,95,98.5),
                ("REIT1",12000,40,45),
                ("ALT2",5000,52,58),
                ("LIQ1",150000,1,1)
        ],

        "preferences":[
            ("EQUITY",30,45),
            ("FIXED_INCOME",25,40),
            ("REAL_ESTATE",8,15),
            ("ALTERNATIVES",5,12),
            ("LIQUIDITY",5,10)
        ],

        "risk_overview":{
            "concentration_pct":"16",
            "concentration_asset":"MSFT",
            "sharpe_ratio":"1.4",
            "value_at_risk":"275",
            "max_drawdown":"5.4"
        }
    }
]

AI_TALKING_POINTS = [

    {
        "client_id": 1,

        "conversation_openers": [
            "Ask about how his technology business has been performing this quarter and whether the planned summer trip with family is finalized. This provides a natural transition into reviewing long-term wealth growth and investment priorities.",
            "Mention the sustainable investment opportunities discussed during the previous meeting and ask whether his ESG investment objectives or liquidity requirements have changed since then."
        ],

        "portfolio_discussion": [
            "Lead with the strong performance of ASML and NVIDIA, highlighting that semiconductor holdings continue to contribute positively to portfolio growth. Explain how the recent market volatility created temporary drawdowns in April before recovering to new highs in July, validating the long-term investment approach.",
            "Discuss that ESG allocations through the ESG Small Cap Fund and Nordea Climate Fund continue to complement the technology portfolio while maintaining diversification. Review the current bond allocation and explain how a gradual shift toward shorter-duration green bonds could improve portfolio efficiency if interest rates remain elevated."
        ],

        "product_introduction": [
            "Introduce a European AI Infrastructure Fund as a complementary investment that benefits from increasing demand for semiconductor manufacturing, cloud infrastructure and artificial intelligence adoption while remaining aligned with the client's long-term growth strategy.",
            "Present a Sustainable Technology Innovation Fund focused on high-quality European companies benefiting from the expanding EU sustainability framework, positioning it as a natural extension of the client's existing ESG-focused investment philosophy."
        ],

        "anticipated_objections": [
            "If the client expresses concerns about high technology valuations, explain that the recommendation focuses on companies with strong earnings growth, healthy balance sheets and long-term structural demand rather than short-term market momentum.",
            "If the client prefers holding additional cash before investing, explain that keeping excess liquidity for extended periods may reduce long-term purchasing power, while phased investments through diversified ESG funds can lower timing risk."
        ]
    },

    {
        "client_id": 2,

        "conversation_openers": [
            "Ask whether her financial priorities or income requirements have changed recently and whether she remains comfortable with the current balance between growth and capital preservation.",
            "Start a discussion about recent developments in the AI industry and ask whether she would like to gain exposure through diversified investments rather than individual technology stocks."
        ],

        "portfolio_discussion": [
            "Highlight that the fixed-income allocation continues to provide portfolio stability while generating consistent income. Explain how the combination of government bonds and short-duration green bonds has reduced overall portfolio volatility during recent market fluctuations.",
            "Review the steady contribution from dividend-paying assets and explain that maintaining a disciplined allocation to income-generating investments continues to support her conservative investment objectives without taking unnecessary market risk."
        ],

        "product_introduction": [
            "Introduce a European Dividend Equity Fund that complements the existing income strategy while providing moderate long-term capital appreciation through financially strong companies with consistent dividend histories.",
            "Recommend an Investment Grade Corporate Bond Portfolio designed to improve portfolio yield while maintaining a conservative risk profile and high credit quality."
        ],

        "anticipated_objections": [
            "If the client is hesitant about increasing equity exposure, explain that the recommendation focuses on diversified dividend-paying companies rather than high-growth technology stocks, helping maintain portfolio stability.",
            "If the client prefers keeping a larger allocation in cash, explain that gradually allocating part of the cash position into high-quality bonds can improve long-term income without materially increasing investment risk."
        ]
    },

    {
        "client_id": 3,

        "conversation_openers": [
            "Ask how retirement planning has progressed over the past few months and whether there have been any changes in family succession or estate planning priorities since the previous review.",
            "Begin the meeting by discussing whether the current portfolio continues to generate sufficient retirement income while preserving capital for future generations."
        ],

        "portfolio_discussion": [
            "Explain that the portfolio continues to maintain a balanced allocation between fixed income, quality equities and real estate investments, supporting capital preservation while generating dependable income throughout retirement.",
            "Review the recent performance of Microsoft, Apple and the bond holdings, demonstrating how the diversified allocation has limited downside during periods of market volatility while continuing to participate in long-term market appreciation."
        ],

        "product_introduction": [
            "Present a High Quality Corporate Bond Strategy focused on enhancing retirement income through diversified investment-grade issuers while maintaining low portfolio volatility.",
            "Introduce a Global Dividend Leaders Fund that emphasizes financially stable companies with long records of increasing dividends, providing an additional source of sustainable retirement income."
        ],

        "anticipated_objections": [
            "If the client is concerned about increasing investment risk after retirement, explain that the proposed recommendations maintain diversification and prioritize capital preservation rather than aggressive growth.",
            "If the client prefers maintaining the current allocation, explain that only small portfolio adjustments are recommended to improve long-term income generation while preserving the existing risk profile."
        ]
    }

]


# ---------------- Seed Function ----------------

def seed_all_clients():

    engine = init_db(DATABASE_URL)
    Session = get_session_factory(engine)

    with Session() as session:

    # ---------------- Seed Themes ----------------
        for theme in THEMES:

            existing_theme = (
                session.query(Theme)
                .filter_by(name=theme["theme_name"])
                .first()
            )

            if not existing_theme:

                session.add(
                    Theme(
                        name=theme["theme_name"],
                        category=theme["category"],
                        description=theme["description"],
                        classification_guidance=theme["classification_guidance"]
                    )
                )

        session.commit()

        print("Themes seeded successfully")

        # Seed Sector Master
        for sector in sector_master:

            existing_sector = session.query(
                SectorMaster
            ).filter_by(
                id=sector["id"]
            ).first()

            if not existing_sector:

                session.add(
                    SectorMaster(
                        id=sector["id"],
                        name=sector["name"],
                        gics_code=sector["gics_code"],
                        description=sector["description"]
                    )
                )

        session.commit()

        # ---------------- Seed Fund List ----------------

        for fund in FUNDS:

            existing_fund = session.query(
                FundList
            ).filter_by(
                fund_id=fund["fund_id"]
            ).first()

            if not existing_fund:

                session.add(
                    FundList(
                        fund_id=fund["fund_id"],
                        fund_name=fund["fund_name"],
                        sector=fund["sector"],
                        risk=fund["risk"],
                        investment_style=fund["investment_style"]
                    )
                )

        session.commit()
        print("Fund list seeded successfully")

        # Seed Securities
        for sec in securities:

            existing_security = session.query(
                Security
            ).filter_by(
                ticker=sec["ticker"]
            ).first()

            if not existing_security:

                session.add(
                    Security(
                        ticker=sec["ticker"],
                        name=sec["name"],
                        security_type=sec["security_type"],
                        exchange=sec["exchange"],
                        sector_id=sec["sector_id"],
                        currency=sec["currency"],
                        last_price=sec["last_price"]
                    )
                )

        session.commit()

        # Seed Security Price History

        for ticker, month, year, price in security_price_history:

            existing_history = session.query(
                SecurityPriceHistory
            ).filter_by(
                ticker=ticker,
                month=month,
                year=year
            ).first()

            if not existing_history:

                session.add(
                    SecurityPriceHistory(
                        ticker=ticker,
                        month=month,
                        year=year,
                        price=price
                    )
                )

        session.commit()

        # ---------------- Seed Transactions ----------------

        for tx in transactions:

            existing_tx = session.query(
                Transaction
            ).filter_by(
                account_id=tx["account_id"],
                ticker=tx["ticker"],
                transaction_date=datetime.strptime(
                    tx["transaction_date"],
                    "%Y-%m-%d"
                ).date()
            ).first()

            if not existing_tx:

                session.add(
                    Transaction(
                        account_id=tx["account_id"],
                        transaction_type=tx["transaction_type"],
                        ticker=tx["ticker"],
                        product_name=tx["product_name"],
                        amount=tx["amount"],
                        currency=tx["currency"],
                        transaction_date=datetime.strptime(
                            tx["transaction_date"],
                            "%Y-%m-%d"
                        ).date()
                    )
                )

        session.commit()

        print("Transactions seeded successfully")

        # Seed Relationship Managers
        for rm in RMS:

            existing_rm = session.query(
                RelationshipManager
            ).filter_by(id=rm["id"]).first()

            if not existing_rm:

                session.add(
                    RelationshipManager(
                        id=rm["id"],
                        rm_code=rm["rm_code"],
                        name=rm["name"]
                    )
                )

        session.commit()

        # Seed Clients

        for data in CLIENTS:

            existing = session.query(
                Client
            ).filter_by(
                client_code=data["code"]
            ).first()

            if existing:
                print(
                    f"[{data['code']}] already exists"
                )
                continue

            client = Client(
                client_code=data["code"],
                name=data["name"],
                rm_id=data["rm_id"],
                risk_profile=data["risk"],
                email=f"{data['code'].lower()}@demo.com",
                phone=data["phone"],
                age=data["age"],
                profession=data["profession"],
                preference=data["preference"],
                service_model=data["service_model"],
                investment_goals=data["investment_goals"]
            )

            session.add(client)
            session.flush()

            # Personal Details

            pd = data["personal_details"]

            session.add(
                ClientPersonalDetails(
                    client_id=client.id,
                    marital_status=pd["marital_status"],
                    kids_details=pd["kids_details"],
                    date_of_Birth=pd["date_of_Birth"],
                    hobbies=pd["hobbies"],
                    other=pd["other"],
                    client_constraints=pd["client_constraints"]
                )
            )

            # Meeting

            meeting = data["meeting"]

            session.add(
                Meeting(
                    rm_id=data["rm_id"],
                    client_id=client.id,
                    title=meeting["title"],
                    date=date.today(),
                    time=time(10,30),
                    location=meeting["location"],
                    platform=meeting["platform"]
                )
            )

            # Meeting Summary

#             summary = data["meeting_summary"]
#
#             session.add(
#                 ClientMeetingSummary(
#                     rm_id=data["rm_id"],
#                     client_id=client.id,
#                     main_discussion_points=summary["discussion_points"],
#                     client_questions=summary["questions"],
#                     last_meeting_date=date.today()
#                 )
#             )

            # Account

            account = Account(
                account_number=f"ACC-{data['code']}-001",
                client_id=client.id,
                account_type=AccountTypeEnum.INDIVIDUAL
            )

            session.add(account)
            session.flush()

            # Portfolio

            total = sum(
                qty*price
                for _,qty,_,price
                in data["holdings"]
            )

            portfolio = Portfolio(
                portfolio_code=f"PF-{data['code']}",
                account_id=account.id,
                name=f"{data['name']} - {data['strategy']}",
                strategy=data["strategy"],
                inception_date=datetime(
                    2024,1,1
                ),
                total_value=total,
                last_valued_at=datetime.utcnow()
            )

            session.add(portfolio)
            session.flush()

            # Holdings

            for ticker,qty,avg_cost,price in data["holdings"]:

                sec = session.query(
                    Security
                ).filter_by(
                    ticker=ticker
                ).first()

                if not sec:
                    print(
                        f"Warning: {ticker} not found"
                    )
                    continue

                sec.last_price = price

                session.add(
                    Holding(
                        portfolio_id=portfolio.id,
                        security_id=sec.id,
                        quantity=qty,
                        avg_cost=avg_cost,
                        current_value=qty*price,
                        weight_pct=(qty*price)/total*100
                    )
                )

            # Client Preferences
            for security_type,bw_min,bw_max in data["preferences"]:

                session.add(
                    ClientPreference(
                        client_id=client.id,
                        security_type=security_type,
                        bandwidth_min=bw_min,
                        bandwidth_max=bw_max
                    )
                )

            # Client Risk Overview
            risk = data["risk_overview"]

            session.add(
                ClientRiskOverview(
                    client_id=client.id,
                    concentration_pct=risk["concentration_pct"],
                    concentration_asset=risk["concentration_asset"],
                    sharpe_ratio=risk["sharpe_ratio"],
                    value_at_risk=risk["value_at_risk"],
                    max_drawdown=risk["max_drawdown"]
                )
            )

            ai_data = next(
                item for item in AI_TALKING_POINTS
                if item["client_id"] == client.id
            )

            session.add(
                ClientAITalkingPoints(
                    client_id=client.id,
                    conversation_openers=ai_data["conversation_openers"],
                    portfolio_discussion=ai_data["portfolio_discussion"],
                    product_introduction=ai_data["product_introduction"],
                    anticipated_objections=ai_data["anticipated_objections"]
                )
            )

            session.commit()

            print(
                f"[{data['code']}] "
                f"{data['name']} seeded"
            )


if __name__ == "__main__":
    seed_all_clients()
    from step3_match import run_matching
    run_matching()
    print("\nDone.")