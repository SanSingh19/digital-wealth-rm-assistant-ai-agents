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
    ClientRiskOverview
)

from config.settings import DATABASE_URL


# ---------------- Relationship Managers ----------------

RMS = [
    {"id": 1, "rm_code": "RM001", "name": "John Smith"},
    {"id": 2, "rm_code": "RM002", "name": "Sarah Lee"},
]

# ---------------- SectorMasters ----------------
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
        "currency": "USD",
        "last_price": 850.0
    },

    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 2,
        "currency": "USD",
        "last_price": 900.0
    },

    {
        "ticker": "MSFT",
        "name": "Microsoft Corporation",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 1,
        "currency": "USD",
        "last_price": 430.0
    },

    {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "security_type": "EQUITY",
        "exchange": "NASDAQ",
        "sector_id": 1,
        "currency": "USD",
        "last_price": 195.0
    },

    {
        "ticker": "BOND1",
        "name": "Euro Gov Bond Fund",
        "security_type": "FIXED_INCOME",
        "exchange": "LSE",
        "sector_id": 3,
        "currency": "USD",
        "last_price": 98.5
    },

    {
        "ticker": "BOND2",
        "name": "Short Duration Green Bond",
        "security_type": "FIXED_INCOME",
        "exchange": "LSE",
        "sector_id": 3,
        "currency": "USD",
        "last_price": 95.0
    },

    {
        "ticker": "REIT1",
        "name": "European Real Estate ETF",
        "security_type": "REAL_ESTATE",
        "exchange": "EURONEXT",
        "sector_id": 9,
        "currency": "USD",
        "last_price": 45.0
    },

    {
        "ticker": "ALT1",
        "name": "ESG Small Cap Fund",
        "security_type": "ALTERNATIVES",
        "exchange": "EURONEXT",
        "sector_id": 12,
        "currency": "USD",
        "last_price": 62.0
    },

    {
        "ticker": "ALT2",
        "name": "Nordea Climate Fund",
        "security_type": "ALTERNATIVES",
        "exchange": "EURONEXT",
        "sector_id": 12,
        "currency": "USD",
        "last_price": 58.0
    },

    {
        "ticker": "LIQ1",
        "name": "Money Market Fund",
        "security_type": "LIQUIDITY",
        "exchange": "EURONEXT",
        "sector_id": 3,
        "currency": "USD",
        "last_price": 1.0
    }
]

# ---------------- Clients ----------------

CLIENTS = [
    {
        "code": "AB345678",
        "name": "Arjun Mehta",
        "risk": "Aggressive",
        "strategy": "Growth",
        "rm_id": 1,
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
                ("ASML",2500,780,850),
                ("NVDA",1500,820,900),
                ("MSFT",2000,390,430),
                ("BOND1",12000,95,98.5),
                ("REIT1",15000,40,45),
                ("ALT1",10000,55,62),
                ("ALT2",8000,52,58),
                ("LIQ1",200000,1,1)
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
        "rm_id":1,
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
                ("AAPL",1000,170,195),
                ("BOND1",25000,94,98.5),
                ("BOND2",22000,90,95),
                ("REIT1",10000,42,45),
                ("ALT1",3000,55,62),
                ("LIQ1",350000,1,1)
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
        "rm_id":2,
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
                    client_code=client.client_code,
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
                    client_id=client.client_code,
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
                    client_id=client.client_code,
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
                        client_id=client.client_code,
                        security_type=security_type,
                        bandwidth_min=bw_min,
                        bandwidth_max=bw_max
                    )
                )

            # Client Risk Overview
            risk = data["risk_overview"]

            session.add(
                ClientRiskOverview(
                    client_id=client.client_code,
                    concentration_pct=risk["concentration_pct"],
                    concentration_asset=risk["concentration_asset"],
                    sharpe_ratio=risk["sharpe_ratio"],
                    value_at_risk=risk["value_at_risk"],
                    max_drawdown=risk["max_drawdown"]
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