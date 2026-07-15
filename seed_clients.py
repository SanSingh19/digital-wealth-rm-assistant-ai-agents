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
    ClientAITalkingPoints
)

from config.settings import DATABASE_URL


# ---------------- Relationship Managers -----------------------

RMS = [
    {"id": 1001, "rm_code": "RM001", "name": "John Smith"},
    {"id": 1002, "rm_code": "RM002", "name": "Sarah Lee"},
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

        "meeting_summary": {
            "discussion_points": [
                  "Client's business performed well in H2 2025 with strong revenue growth.",
                  "Client accumulated €800K cash from dividends and business income and wanted to deploy it.",
                  "Preference to increase sustainable European equity exposure, especially technology and green energy.",
                  "Discussed impact of ECB rate trajectory on bond allocation.",
                  "Agreed that RM would prepare specific ESG small-cap options for the next meeting."
            ],
            "questions": [
                        "What is the outlook for European sustainable tech?",
                        "Should I reduce my bond allocation given the rate environment?"
            ]
        },

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

        "meeting_summary":{
            "discussion_points":["Client focused on stable income investments.",
                                 "Discussed dividend-paying healthcare and banking stocks.",
                                 "Reviewed current bond allocation strategy.",
                                 "Explored tax-efficient portfolio options."],
            "questions":[
                         "Should I add healthcare exposure?",
                         "What is the expected dividend outlook next year?"]
        },

        "holdings":[

            ("AAPL",12000,170,195),
            ("BOND1",18000,94,98.5),
            ("BOND2",14000,90,95),
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

        "meeting_summary":{
            "discussion_points":[ "Reviewed retirement income sustainability.",
                                   "Discussed balancing equity exposure with fixed income holdings.",
                                   "Evaluated dividend strategies for stable cash flow.",
                                   "Reviewed succession and estate planning considerations.",
                                   "RM to provide tax-efficient income strategies."],
            "questions":["Can I improve portfolio income without increasing risk?",
                         "Should I increase fixed income exposure?"]
        },

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

            summary = data["meeting_summary"]

            session.add(
                ClientMeetingSummary(
                    rm_id=data["rm_id"],
                    client_id=client.id,
                    main_discussion_points=summary["discussion_points"],
                    client_questions=summary["questions"],
                    last_meeting_date=date.today()
                )
            )

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