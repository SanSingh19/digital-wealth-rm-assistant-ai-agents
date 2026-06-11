# ─────────────────────────────────────────────
#  Finance Pipeline  ·  Configuration
# ─────────────────────────────────────────────
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── RSS Sources ────────────────────────────────
RSS_SOURCES = [
    {
        "name": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex",
        "enabled": True,
    },
    {
        "name": "Yahoo Finance Markets",
        "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?region=US&lang=en-US",
        "enabled": True,
    },
]

# ── Storage ────────────────────────────────────
RAW_FEED_DIR   = BASE_DIR / "data" / "raw_feeds"    # XML dumps
ARTICLES_DIR   = BASE_DIR / "data" / "articles"     # per-article JSON
LOG_DIR        = BASE_DIR / "logs"

# ── Database ───────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///finance_pipeline.db"          # swap for postgres in prod
)
# Postgres example:
# DATABASE_URL = "postgresql://user:pass@localhost:5432/finance_db"

# ── OpenAI ────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-your-openai-key-here")
OPENAI_MODEL   = "gpt-4o"
MAX_ARTICLES_PER_RUN = 10          # articles sent to AI per job run

# ── Scheduler ─────────────────────────────────
SCHEDULE_INTERVAL_MINUTES = 1440    # how often the full pipeline runs(1 Day)

# ── Ingestion fetch settings ───────────────────
REQUEST_TIMEOUT  = 15              # seconds
REQUEST_HEADERS  = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; FinancePipeline/1.0; "
        "+https://yourcompany.com/bot)"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}
