# ─────────────────────────────────────────────
#  Finance Pipeline  ·  Configuration
# ─────────────────────────────────────────────

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import os
from pathlib import Path
from dotenv import load_dotenv

import os
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


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
    {
        "name": "Markets News",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "enabled": True,
    },
    {
        "name": "Google News",
        "url": "https://news.google.com/rss/search?q=when:24h+site:reuters.com/world/india&ceid=US:en&hl=en-US&gl=US",
        "enabled": True,
    }
]

# ── Storage ────────────────────────────────────
RAW_FEED_DIR   = BASE_DIR / "data" / "raw_feeds"    # XML dumps
ARTICLES_DIR   = BASE_DIR / "data" / "articles"     # per-article JSON
LOG_DIR        = BASE_DIR / "logs"

# ── Database ───────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///test.db"          # swap for postgres in prod
)
# Postgres example:
# DATABASE_URL = "postgresql://user:pass@localhost:5432/finance_db"

# ── OpenAI ────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-your-openai-key-here")
OPENAI_MODEL   = "gpt-4o"
MAX_ARTICLES_PER_RUN = 10          # articles sent to AI per job run

# ── Anthropic Claude ──────────────────────────
# CHANGED (Claude via Azure AI Foundry): this deployment is not called on
# api.anthropic.com directly - it's an Azure AI Foundry resource, which uses a
# different base URL (https://<resource>.services.ai.azure.com/anthropic/) and
# accepts the Foundry resource key as the api key. ANTHROPIC_API_KEY here is that
# Foundry resource key, not a direct api.anthropic.com key.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "sk-ant-your-anthropic-key-here")
CLAUDE_MODEL = os.getenv( "CLAUDE_MODEL", "claude-sonnet-5-5")
ANTHROPIC_FOUNDRY_RESOURCE = os.getenv("ANTHROPIC_FOUNDRY_RESOURCE", "claude2026-resource")
ANTHROPIC_BASE_URL = f"https://{ANTHROPIC_FOUNDRY_RESOURCE}.services.ai.azure.com/anthropic"

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
