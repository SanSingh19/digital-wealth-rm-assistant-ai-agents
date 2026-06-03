"""
step1_ingest.py  –  Yahoo Finance RSS Ingestion

Flow:
  1. Fetch RSS feed  (feedparser + custom headers)
  2. For each entry → scrape full article text with newspaper3k
  3. Save  <title>.json  to  data/articles/YYYY-MM-DD/
  4. Persist NewsArticle row to DB  (skip duplicates via guid)
  5. Dump raw XML feed to  data/raw_feeds/  for audit trail
"""

import re
import json
import hashlib
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

import feedparser
import requests

# newspaper3k (aliased as newspaper)
try:
    from newspaper import Article as NewspaperArticle
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

from sqlalchemy.orm import Session

# ── local imports ──────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.settings import (
    RSS_SOURCES, RAW_FEED_DIR, ARTICLES_DIR, LOG_DIR,
    DATABASE_URL, REQUEST_TIMEOUT, REQUEST_HEADERS,
    MAX_ARTICLES_PER_RUN,
)
from models import NewsArticle, init_db, get_session_factory

# ── logging ────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "ingest.log"),
    ],
)
log = logging.getLogger("ingest")


# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

def slugify_title(title: str, max_len: int = 80) -> str:
    """Turn article title into a safe filename stem."""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_-]+", "_", slug).strip("_")
    return slug[:max_len]


def make_guid(entry) -> str:
    """Stable unique ID: prefer RSS guid, fallback to link hash."""
    raw = getattr(entry, "id", None) or getattr(entry, "link", "")
    if not raw:
        raw = entry.get("title", "") + entry.get("published", "")
    return hashlib.sha256(raw.encode()).hexdigest()


def parse_published(entry) -> datetime | None:
    """Parse RSS date string into a datetime."""
    import email.utils
    raw = getattr(entry, "published", None)
    if not raw:
        return None
    try:
        return datetime(*email.utils.parsedate(raw)[:6])
    except Exception:
        return None


# ══════════════════════════════════════════════
#  FETCH RSS
# ══════════════════════════════════════════════

def fetch_feed(source: dict) -> list[dict]:
    """
    Fetch RSS from source["url"] and return a list of normalised entry dicts.
    Falls back to mock data when the URL is unreachable (useful for local dev /
    sandbox environments where Yahoo blocks egress).
    """
    url  = source["url"]
    name = source["name"]
    log.info(f"Fetching RSS  → {name}  ({url})")

    # ── save raw XML ───────────────────────────
    RAW_FEED_DIR.mkdir(parents=True, exist_ok=True)
    ts       = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    raw_path = RAW_FEED_DIR / f"{slugify_title(name)}_{ts}.xml"

    raw_content = b""
    try:
        resp = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        raw_content = resp.content
        raw_path.write_bytes(raw_content)
        log.info(f"  Raw XML saved → {raw_path.name}  ({len(raw_content)} bytes)")
    except Exception as exc:
        log.warning(f"  Live fetch failed: {exc} – using mock data for dev/demo")
        return _mock_entries(source)

    # ── parse ──────────────────────────────────
    feed    = feedparser.parse(raw_content)
    entries = feed.entries
    log.info(f"  Parsed {len(entries)} entries")
    if not entries:
        log.warning("  Empty feed – using mock data")
        return _mock_entries(source)

    return [_normalise_entry(e, name) for e in entries]


def _normalise_entry(entry, source_name: str) -> dict:
    return {
        "guid":         make_guid(entry),
        "source_name":  source_name,
        "title":        getattr(entry, "title", "(no title)"),
        "summary":      getattr(entry, "summary", ""),
        "url":          getattr(entry, "link", ""),
        "published_at": parse_published(entry),
    }


# ══════════════════════════════════════════════
#  ARTICLE FULL-TEXT SCRAPE
# ══════════════════════════════════════════════

def scrape_full_text(url: str) -> str:
    """Use newspaper3k to fetch and parse full article body."""
    if not NEWSPAPER_AVAILABLE or not url:
        return ""
    try:
        art = NewspaperArticle(url)
        art.download()
        art.parse()
        return art.text
    except Exception as exc:
        log.debug(f"  newspaper3k scrape failed for {url}: {exc}")
        return ""


# ══════════════════════════════════════════════
#  SAVE TO DISK  (data/articles/YYYY-MM-DD/<title>.json)
# ══════════════════════════════════════════════

def save_article_to_disk(article_data: dict) -> Path:
    """
    Saves one article as JSON.
    Filename format:  <slug>__<guid[:8]>.json
    Returns the saved path.
    """
    pub_date = article_data.get("published_at") or datetime.utcnow()
    date_dir = ARTICLES_DIR / pub_date.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    title = article_data.get("title", "untitled")
    slug  = slugify_title(title)
    guid8 = article_data["guid"][:8]
    fname = f"{slug}__{guid8}.json"
    fpath = date_dir / fname

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(
            {**article_data,
             "published_at": (article_data["published_at"].isoformat()
                              if article_data.get("published_at") else None),
             "ingested_at":  datetime.utcnow().isoformat()},
            f, indent=2, ensure_ascii=False,
        )
    return fpath


# ══════════════════════════════════════════════
#  PERSIST TO DB
# ══════════════════════════════════════════════

def persist_article(session: Session, article_data: dict, file_path: Path) -> NewsArticle | None:
    """
    Insert NewsArticle row.  Returns None if guid already exists (duplicate skip).
    """
    existing = session.query(NewsArticle).filter_by(guid=article_data["guid"]).first()
    if existing:
        log.debug(f"  Duplicate guid – skipping: {article_data['title'][:60]}")
        return None

    row = NewsArticle(
        guid          = article_data["guid"],
        source_name   = article_data["source_name"],
        title         = article_data["title"],
        summary       = article_data.get("summary", ""),
        full_text     = article_data.get("full_text", ""),
        url           = article_data.get("url", ""),
        published_at  = article_data.get("published_at"),
        raw_file_path = str(file_path),
        is_processed  = False,
    )
    session.add(row)
    return row


# ══════════════════════════════════════════════
#  MAIN INGESTION FUNCTION
# ══════════════════════════════════════════════

def run_ingestion(limit: int = MAX_ARTICLES_PER_RUN) -> list[int]:
    """
    Full Step-1 pipeline.

    Returns list of newly inserted NewsArticle IDs.
    """
    log.info("═" * 60)
    log.info("STEP 1 · INGESTION  START")
    log.info("═" * 60)

    engine          = init_db(DATABASE_URL)
    SessionFactory  = get_session_factory(engine)

    new_ids: list[int] = []

    with SessionFactory() as session:
        for source in RSS_SOURCES:
            if not source.get("enabled"):
                continue

            entries = fetch_feed(source)
            log.info(f"  Processing {min(len(entries), limit)} / {len(entries)} entries from {source['name']}")

            for entry in entries[:limit]:
                # ── optionally scrape full text ──
                entry["full_text"] = scrape_full_text(entry["url"])

                # ── save file ───────────────────
                fpath = save_article_to_disk(entry)
                log.info(f"  ✔ saved  {fpath.name}")

                # ── persist to DB ────────────────
                row = persist_article(session, entry, fpath)
                if row:
                    session.flush()
                    new_ids.append(row.id)
                    log.info(f"  ✔ DB insert  id={row.id}  title='{entry['title'][:55]}...'")

        session.commit()

    log.info(f"\nSTEP 1 DONE  →  {len(new_ids)} new articles ingested")
    return new_ids


# ══════════════════════════════════════════════
#  MOCK DATA  (used when feed URL is blocked)
# ══════════════════════════════════════════════

def _mock_entries(source: dict) -> list[dict]:
    """Realistic sample articles for local dev / sandbox."""
    import hashlib
    from datetime import timedelta

    samples = [
        ("NVIDIA surpasses $3 trillion market cap on AI chip demand surge",
         "NVIDIA's market valuation crossed the $3 trillion mark as institutional investors "
         "piled into the stock following record data-center revenue guidance."),
        ("Federal Reserve holds rates steady, hints at September cut",
         "Fed Chair Powell signaled the central bank is watching inflation data carefully "
         "before committing to a rate reduction cycle."),
        ("Apple unveils AI-powered iPhone 17 lineup at WWDC 2026",
         "Apple's new iPhone integrates on-device large language models, boosting privacy "
         "and reducing cloud dependency for everyday AI tasks."),
        ("Oil prices drop 4% as OPEC+ agrees to increase output quotas",
         "The cartel's unexpected decision to raise production targets sent crude futures "
         "tumbling, impacting energy sector stocks globally."),
        ("Microsoft Azure cloud revenue up 35% YoY, beating estimates",
         "Strong enterprise AI workload adoption drove Microsoft's cloud segment well ahead "
         "of analyst forecasts, lifting the broader tech sector."),
        ("Tesla Q1 deliveries miss expectations amid pricing pressure",
         "The EV maker delivered fewer vehicles than Wall Street projected as competition "
         "from Chinese manufacturers and softening demand weighed on results."),
        ("Semiconductor shortage eases as TSMC expands Arizona fab capacity",
         "TSMC's $40 billion Arizona investment begins bearing fruit with advanced node "
         "chips rolling off lines, easing supply constraints for key customers."),
        ("JPMorgan warns of recession risk as yield curve inverts further",
         "The bank's chief economist flagged mounting risks in the credit markets and "
         "highlighted the sustained inversion of the 2-10 year Treasury spread."),
        ("Amazon acquires AI startup Adept for $1.2 billion",
         "The deal gives Amazon access to enterprise AI agents capable of operating "
         "software autonomously, deepening its cloud-AI stack against Microsoft and Google."),
        ("Renewable energy stocks rally on new IRA extension proposals",
         "Solar and wind equities jumped after bipartisan support emerged for extending "
         "Inflation Reduction Act clean-energy credits through 2035."),
    ]

    now     = datetime.utcnow()
    results = []
    for i, (title, summary) in enumerate(samples):
        fake_url = f"https://finance.yahoo.com/news/mock-article-{i+1}"
        guid     = hashlib.sha256(title.encode()).hexdigest()
        results.append({
            "guid":         guid,
            "source_name":  source["name"],
            "title":        title,
            "summary":      summary,
            "url":          fake_url,
            "published_at": now - timedelta(hours=i * 2),
        })
    return results


# ══════════════════════════════════════════════
#  CLI ENTRY POINT
# ══════════════════════════════════════════════
if __name__ == "__main__":
    ids = run_ingestion()
    print(f"\n✅  Ingested {len(ids)} new articles  →  IDs: {ids}")
