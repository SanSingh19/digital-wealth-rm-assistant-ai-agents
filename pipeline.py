"""
pipeline.py  –  Scheduler & Orchestrator

Runs the full pipeline on a schedule:

  Step 1 (Ingest)   ->  Step 2 (AI Process)

Usage
-----
  # Run once immediately
  python pipeline.py --run-once

  # Start scheduler (default: every 30 min)
  python pipeline.py

  # Seed demo client/portfolio data
  python pipeline.py --seed-demo

  # Query results
  python pipeline.py --report
"""

import argparse
import logging
import sys
import time

# Fix Windows terminal encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from datetime import datetime
from pathlib import Path
import json

import schedule

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.settings import SCHEDULE_INTERVAL_MINUTES, DATABASE_URL, LOG_DIR
from models import (
    init_db, get_session_factory,
    Client, Account, Portfolio, Holding, Security, SectorMaster,
    AccountTypeEnum, Theme, SectorTag, Trend, MarketEvent, NewsArticle, ClientThemeMatch,
)
from step1_ingest  import run_ingestion
from step2_process import run_processing
from step3_match import run_matching

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)),
        logging.FileHandler(LOG_DIR / "pipeline.log"),
    ],
)
log = logging.getLogger("pipeline")


# ==============================================
#  FULL PIPELINE JOB
# ==============================================

def run_pipeline():
    log.info("\n" + "+" + "=" * 58 + "+")
    log.info(f"|  FINANCE PIPELINE RUN  -  {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  |")
    log.info("+" + "=" * 58 + "+\n")

    try:
        # -- Step 1: Ingest ---------------------
        new_ids = run_ingestion()

        # -- Step 2: AI Process -----------------
        if new_ids:
            run_processing(article_ids=new_ids)
        else:
            log.info("No new articles to process.")

        # -- Step 3: Match clients to themes --------
        log.info("[Step 3] Matching client holdings to themes...")
        match_results = run_matching()
        total_matches = sum(len(v) for v in match_results.values())
        log.info(f"[Step 3] Done. {len(match_results)} client(s), {total_matches} theme match(es).")

        log.info("\n[OK]  Pipeline run completed successfully.\n")


    except Exception as exc:
        log.error(f"[ERROR]  Pipeline error: {exc}", exc_info=True)


# ==============================================
#  DEMO DATA SEED
# ==============================================

def seed_demo_data():
    """Seed a sample client, portfolio, and securities."""
    log.info("Seeding demo client / portfolio data ...")

    engine         = init_db(DATABASE_URL)
    SessionFactory = get_session_factory(engine)

    with SessionFactory() as session:

        # -- Sectors ----------------------------
        sectors_data = [
            ("Technology",        "45"),
            ("Semiconductors",    "45301"),
            ("Financials",        "40"),
            ("Energy",            "10"),
            ("Healthcare",        "35"),
            ("Consumer Discretionary", "25"),
            ("Industrials",       "20"),
            ("Utilities",         "55"),
            ("Real Estate",       "60"),
            ("Communication Services", "50"),
            ("Materials",         "15"),
            ("Renewable Energy",  "10RE"),
        ]
        sector_map = {}
        for name, code in sectors_data:
            s = session.query(SectorMaster).filter_by(name=name).first()
            if not s:
                s = SectorMaster(name=name, gics_code=code)
                session.add(s)
        session.flush()
        for name, _ in sectors_data:
            s = session.query(SectorMaster).filter_by(name=name).first()
            sector_map[name] = s

        # -- Securities -------------------------
        securities_data = [
            ("NVDA",  "NVIDIA Corporation",           "EQUITY", "NASDAQ", "Semiconductors"),
            ("MSFT",  "Microsoft Corporation",        "EQUITY", "NASDAQ", "Technology"),
            ("AAPL",  "Apple Inc.",                   "EQUITY", "NASDAQ", "Technology"),
            ("AMZN",  "Amazon.com Inc.",              "EQUITY", "NASDAQ", "Technology"),
            ("TSLA",  "Tesla Inc.",                   "EQUITY", "NASDAQ", "Consumer Discretionary"),
            ("JPM",   "JPMorgan Chase & Co.",         "EQUITY", "NYSE",   "Financials"),
            ("XOM",   "Exxon Mobil Corporation",      "EQUITY", "NYSE",   "Energy"),
            ("JNJ",   "Johnson & Johnson",            "EQUITY", "NYSE",   "Healthcare"),
            ("ENPH",  "Enphase Energy Inc.",          "EQUITY", "NASDAQ", "Renewable Energy"),
            ("AMD",   "Advanced Micro Devices Inc.",  "EQUITY", "NASDAQ", "Semiconductors"),
        ]
        security_map = {}
        for ticker, name, stype, exchange, sector_name in securities_data:
            sec = session.query(Security).filter_by(ticker=ticker).first()
            if not sec:
                sec = Security(
                    ticker        = ticker,
                    name          = name,
                    security_type = stype,
                    exchange      = exchange,
                    sector_id     = sector_map.get(sector_name, sector_map.get("Technology")).id,
                )
                session.add(sec)
        session.flush()
        for ticker, *_ in securities_data:
            security_map[ticker] = session.query(Security).filter_by(ticker=ticker).first()

        # -- Client 1 ---------------------------
        client1 = session.query(Client).filter_by(client_code="C001").first()
        if not client1:
            client1 = Client(
                client_code  = "C001",
                name         = "Arjun Mehta",
                email        = "arjun.mehta@example.com",
                phone        = "+91-98200-00001",
                risk_profile = "Aggressive",
            )
            session.add(client1)
            session.flush()

            account1 = Account(
                account_number = "ACC-C001-001",
                client_id      = client1.id,
                account_type   = AccountTypeEnum.INDIVIDUAL,
                currency       = "USD",
            )
            session.add(account1)
            session.flush()

            portfolio1 = Portfolio(
                portfolio_code = "PF-C001-GROWTH",
                account_id     = account1.id,
                name           = "Arjun – US Growth Portfolio",
                strategy       = "Growth",
                inception_date = datetime(2023, 1, 1),
                total_value    = 500_000.0,
                last_valued_at = datetime.utcnow(),
            )
            session.add(portfolio1)
            session.flush()

            holdings_data = [
                ("NVDA", 200,  85.0, 900.0),
                ("MSFT", 150, 310.0, 430.0),
                ("AAPL", 100, 170.0, 195.0),
                ("AMD",  300,  95.0, 162.0),
                ("ENPH",  50, 200.0, 115.0),
            ]
            for ticker, qty, avg_cost, price in holdings_data:
                sec = security_map[ticker]
                sec.last_price    = price
                sec.last_price_at = datetime.utcnow()
                session.add(Holding(
                    portfolio_id  = portfolio1.id,
                    security_id   = sec.id,
                    quantity      = qty,
                    avg_cost      = avg_cost,
                    current_value = qty * price,
                    weight_pct    = (qty * price) / 500_000 * 100,
                ))

        session.commit()
        log.info("  >> Demo data seeded: Client C001, Account ACC-C001-001, Portfolio PF-C001-GROWTH")


# ==============================================
#  REPORT
# ==============================================

def print_report():
    """Print a readable summary of current DB state."""
    engine         = init_db(DATABASE_URL)
    SessionFactory = get_session_factory(engine)

    with SessionFactory() as session:
        articles = session.query(NewsArticle).count()
        events   = session.query(MarketEvent).count()
        trends   = session.query(Trend).count()
        themes   = session.query(Theme).count()
        tags     = session.query(SectorTag).count()

        print("\n" + "=" * 60)
        print("  FINANCE PIPELINE  -  DATABASE SUMMARY")
        print("=" * 60)
        print(f"  NewsArticles   : {articles}")
        print(f"  MarketEvents   : {events}")
        print(f"  Trends         : {trends}")
        print(f"  Themes         : {themes}")
        print(f"  SectorTags     : {tags}")

        # Investment Themes
        print("\n" + "=" * 60)
        print("  INVESTMENT THEMES  ->  SECTORS")
        print("=" * 60)
        all_themes = session.query(Theme).all()
        if not all_themes:
            print("\n  (no themes yet - run: python pipeline.py --run-once)")
        for theme in all_themes:
            print(f"\n  >> {theme.name}")
            desc = (theme.description or "")[:120]
            if desc:
                print(f"     {desc}")
            for tag in session.query(SectorTag).filter_by(theme_id=theme.id).all():
                filled = int(tag.confidence * 10)
                bar    = "#" * filled + "." * (10 - filled)
                print(f"     - {tag.sector_name:<28}  {tag.sentiment.value:<10}  [{bar}]  {tag.confidence:.0%}")

        # Trends
        print("\n" + "=" * 60)
        print("  TRENDS")
        print("=" * 60)
        all_trends = session.query(Trend).all()
        if not all_trends:
            print("\n  (no trends yet)")
        for t in all_trends:
            ev_count = len(t.event_links)
            print(f"\n  [{t.direction.value}] {t.name}  ({ev_count} events)")
            if t.description:
                print(f"    {t.description[:100]}")

        # Articles
        print("\n" + "=" * 60)
        print("  ARTICLES  ->  EVENTS")
        print("=" * 60)
        for art in session.query(NewsArticle).limit(15).all():
            ev_count  = len(art.market_events)
            processed = "[DONE]" if art.is_processed else "[WAIT]"
            print(f"  {processed}  [{art.id:3d}]  {art.title[:55]:55s}  ({ev_count} events)")

        print("\n" + "=" * 60)

        # Client-Theme Matches
        print("\n" + "=" * 60)
        print(" CLIENT → THEME MATCHES")
        print("=" * 60)
        all_clients = session.query(Client).all()
        if not all_clients:
            print("\n (no clients seeded yet)")
        for client in all_clients:
            matches = (
                session.query(ClientThemeMatch)
                .filter_by(client_id=client.id)
                .order_by(ClientThemeMatch.exposure_pct.desc())
                .all()
            )
            print(f"\n  [{client.client_code}] {client.name}  ({client.risk_profile})")
            if not matches:
                print("    (no matches yet — run pipeline once)")
            for m in matches:
                theme = session.query(Theme).get(m.theme_id)
                sectors = json.loads(m.matched_sectors or "[]")
                bar = "#" * int(m.confidence * 10) + "." * (10 - int(m.confidence * 10))
                sentiment_str = m.sentiment.value if m.sentiment else "N/A"
                print(f"    >> {theme.name:<30}  {sentiment_str:<10}  "
                    f"[{bar}]  ₹{m.exposure_value:>10,.0f}  ({m.exposure_pct:.1f}%)")
                print(f"       Sectors: {', '.join(sectors)}")

def start_scheduler():
    log.info(f"Starting scheduler – interval: every {SCHEDULE_INTERVAL_MINUTES} minutes")
    schedule.every(SCHEDULE_INTERVAL_MINUTES).minutes.do(run_pipeline)

    # Run immediately on start
    run_pipeline()

    while True:
        schedule.run_pending()
        time.sleep(30)


# ==============================================
#  CLI
# ==============================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finance Intelligence Pipeline")
    parser.add_argument("--run-once",   action="store_true", help="Run pipeline once and exit")
    parser.add_argument("--seed-demo",  action="store_true", help="Seed demo client/portfolio data")
    parser.add_argument("--report",     action="store_true", help="Print DB summary report")
    parser.add_argument("--init-db",    action="store_true", help="Initialise DB tables only")
    args = parser.parse_args()

    if args.init_db:
        init_db(DATABASE_URL)
        log.info("Database tables created.")

    elif args.seed_demo:
        init_db(DATABASE_URL)
        seed_demo_data()
        run_matching()

    elif args.report:
        print_report()

    elif args.run_once:
        init_db(DATABASE_URL)
        run_pipeline()

    else:
        init_db(DATABASE_URL)
        start_scheduler()