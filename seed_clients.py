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
    ClientMeetingSummary
)

from config.settings import DATABASE_URL


# ---------------- Relationship Managers ----------------

RMS = [
    {"id": 1, "rm_code": "RM001", "name": "John Smith"},
    {"id": 2, "rm_code": "RM002", "name": "Sarah Lee"},
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
            ("NVDA",200,85,900),
            ("MSFT",150,310,430),
            ("AMD",300,95,162),
            ("ENPH",50,200,115)
        ]
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
            ("JNJ",100,155,165),
            ("JPM",80,140,195),
            ("XOM",120,55,115)
        ]
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
            ("AAPL",50,170,195),
            ("JPM",60,140,195),
            ("AMZN",30,130,185),
            ("XOM",40,55,115)
        ]
    }
]


# ---------------- Seed Function ----------------

def seed_all_clients():

    engine = init_db(DATABASE_URL)
    Session = get_session_factory(engine)

    with Session() as session:

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