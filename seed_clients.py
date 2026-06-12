"""
seed_clients.py – Seed multiple demo clients with different portfolios.

Usage: python seed_clients.py
"""

from datetime import datetime
from models import init_db, get_session_factory, Client, Account, Portfolio, \
    Holding, Security, SectorMaster, AccountTypeEnum
from config.settings import DATABASE_URL

CLIENTS = [
    {
        "code": "C001", "name": "Arjun Mehta",
        "risk": "Aggressive", "strategy": "Growth",
        "holdings": [("NVDA",200,85,900), ("MSFT",150,310,430),
                     ("AMD",300,95,162), ("ENPH",50,200,115)],
    },
    {
        "code": "C002", "name": "Priya Sharma",
        "risk": "Conservative", "strategy": "Income",
        "holdings": [("JNJ",100,155,165), ("JPM",80,140,195),
                     ("XOM",120,55,115)],
    },
    {
        "code": "C003", "name": "Rahul Gupta",
        "risk": "Moderate", "strategy": "Balanced",
        "holdings": [("AAPL",50,170,195), ("JPM",60,140,195),
                     ("AMZN",30,130,185), ("XOM",40,55,115)],
    },
    {
        "code": "C004", "name": "Neha Joshi",
        "risk": "Aggressive", "strategy": "Tech-Heavy",
        "holdings": [("NVDA",500,85,900), ("AMD",400,95,162),
                     ("MSFT",200,310,430), ("AMZN",100,130,185)],
    },
    {
        "code": "C005", "name": "Vikram Patel",
        "risk": "Conservative", "strategy": "ESG",
        "holdings": [("ENPH",200,200,115), ("JNJ",150,155,165),
                     ("MSFT",80,310,430)],
    },
]

def seed_all_clients():
    engine = init_db(DATABASE_URL)
    Session = get_session_factory(engine)
    with Session() as session:
        for data in CLIENTS:
            if session.query(Client).filter_by(client_code=data["code"]).first():
                print(f"  [{data['code']}] already exists, skipping.")
                continue

            client = Client(
                client_code=data["code"], name=data["name"],
                risk_profile=data["risk"],
                email=f"{data['code'].lower()}@demo.com"
            )
            session.add(client); session.flush()

            account = Account(
                account_number=f"ACC-{data['code']}-001",
                client_id=client.id,
                account_type=AccountTypeEnum.INDIVIDUAL,
            )
            session.add(account); session.flush()

            total = sum(qty * price for (_, qty, _, price) in data["holdings"])
            portfolio = Portfolio(
                portfolio_code=f"PF-{data['code']}",
                account_id=account.id,
                name=f"{data['name']} – {data['strategy']}",
                strategy=data["strategy"],
                inception_date=datetime(2024, 1, 1),
                total_value=total,
                last_valued_at=datetime.utcnow(),
            )
            session.add(portfolio); session.flush()

            for ticker, qty, avg_cost, price in data["holdings"]:
                sec = session.query(Security).filter_by(ticker=ticker).first()
                if not sec:
                    print(f"    Warning: ticker {ticker} not found, skipping.")
                    continue
                sec.last_price = price
                session.add(Holding(
                    portfolio_id=portfolio.id,
                    security_id=sec.id,
                    quantity=qty,
                    avg_cost=avg_cost,
                    current_value=qty * price,
                    weight_pct=(qty * price) / total * 100,
                ))

            session.commit()
            print(f"  [{data['code']}] {data['name']} seeded.")

if __name__ == "__main__":
    seed_all_clients()
    from step3_match import run_matching
    run_matching()
    print("\nDone. Run: python pipeline.py --report")