"""
step2_process.py  –  AI-Powered Market Intelligence Extraction

Flow per batch of unprocessed NewsArticles:
  ┌---------------------------------------------------------┐
  │  NewsArticle  (title + summary + full_text)             │
  │      │                                                  │
  │      ▼  Claude Sonnet                                   │
  │  MarketEvents[]  (discrete events from article)         │
  │      │                                                  │
  │      ▼  Claude Sonnet  (batch)                          │
  │  Trends[]   (cross-article patterns)                    │
  │      │                                                  │
  │      ▼  Claude Sonnet                                   │
  │  Themes[]   (high-level investment narratives)          │
  │      │                                                  │
  │      ▼                                                  │
  │  SectorTag[]   (sector + sentiment per Theme)           │
  ----------------------------------------------------------┘

All entities + relationships persisted to SQLite / Postgres.
"""

import json
import logging
import sys
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.settings import (
    DATABASE_URL, OPENAI_API_KEY, OPENAI_MODEL,
    MAX_ARTICLES_PER_RUN, LOG_DIR,
)
from models import (
    NewsArticle, MarketEvent, Trend, MarketEventTrend,
    Theme, TrendTheme, SectorTag, SentimentEnum, TrendDirectionEnum,
    init_db, get_session_factory,
)

# -- logging ------------------------------------
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)),
        logging.FileHandler(LOG_DIR / "process.log"),
    ],
)
log = logging.getLogger("process")


# ==============================================
#  OPENAI CLIENT
# ==============================================

def get_openai_client() -> OpenAI:
    api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "sk-your-openai-key-here":
        raise RuntimeError(
            "OPENAI_API_KEY not set. "
            "Export it or update OPENAI_API_KEY in config/settings.py"
        )
    return OpenAI(api_key=api_key)


def openai_json(client: OpenAI, prompt: str, system: str) -> Any:
    """
    Call OpenAI and parse the response as JSON.
    Retries once on JSON decode failure.
    """
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model           = OPENAI_MODEL,
                max_tokens      = 2048,
                response_format = {"type": "json_object"},
                messages        = [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
            )
            raw = resp.choices[0].message.content.strip()
            # strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw.strip())
            # OpenAI json_object mode wraps arrays in a dict key -- unwrap
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
            if isinstance(parsed, dict):
                for v in parsed.values():
                    if isinstance(v, list):
                        valid = [item for item in v if isinstance(item, dict)]
                        return valid
                return []
            return []
        except json.JSONDecodeError as e:
            if attempt == 0:
                log.warning(f"JSON decode error, retrying: {e}")
                time.sleep(1)
                continue
            raise
        except Exception as e:
            if "rate_limit" in str(e).lower():
                log.warning("Rate limit hit, sleeping 30s")
                time.sleep(30)
            raise


# ==============================================
#  STAGE A  –  EXTRACT MARKET EVENTS FROM ARTICLE
# ==============================================

SYSTEM_MARKET_EVENTS = """
You are a senior financial analyst AI.
Your job is to extract discrete market events from a news article.
Respond ONLY with valid JSON – no preamble, no markdown fences.
""".strip()

PROMPT_MARKET_EVENTS = """
Article title:   {title}
Article summary: {summary}
Article text:    {body}

Extract all distinct market events mentioned.
A market event is a specific, factual occurrence with market implications
(earnings, rate decisions, M&A deals, product launches, regulatory actions, etc.).

Return a JSON object with a single key "events" containing an array:
{{
  "events": [
    {{
      "event_text":  "<one-sentence description of the event>",
      "event_type":  "<one of: EARNINGS | MACRO | M_AND_A | REGULATORY | PRODUCT | SUPPLY_CHAIN | GEOPOLITICAL | OTHER>",
      "entities":    ["<ticker or company name>", ...]
    }}
  ]
}}

Return {{"events": []}} if no clear market events are found.
""".strip()


def extract_market_events(client, article: NewsArticle):
    body = (article.full_text or article.summary or "")[:3000]  # cap tokens
    prompt = PROMPT_MARKET_EVENTS.format(
        title   = article.title,
        summary = article.summary or "",
        body    = body,
    )
    result = openai_json(client, prompt, SYSTEM_MARKET_EVENTS)
    if not isinstance(result, list):
        return []
    return result


# ==============================================
#  STAGE B  –  CLUSTER EVENTS INTO TRENDS
# ==============================================

SYSTEM_TRENDS = """
You are a financial markets strategist AI.
Your job is to identify emerging trends from a collection of market events.
Respond ONLY with valid JSON – no preamble, no markdown fences.
""".strip()

PROMPT_TRENDS = """
Here are {n} market events extracted from recent financial news:

{events_block}

Group these events into named market TRENDS.
A trend is a repeating pattern or directional force across multiple events
(e.g. "AI Infrastructure Build-Out", "Central Bank Policy Pivot").

Return a JSON object with a single key "trends" containing an array:
{{
  "trends": [
    {{
      "trend_name":        "<short memorable name>",
      "trend_description": "<2-3 sentence description>",
      "direction":         "<Bullish | Bearish | Sideways | Unknown>",
      "event_indices":     [<0-based indices of events that belong to this trend>],
      "relevance_scores":  [<0.0-1.0 confidence for each event in event_indices>]
    }}
  ]
}}
""".strip()


def cluster_into_trends(client, events_with_ids):
    if not events_with_ids:
        return []
    lines = [f"[{i}] ({e['event_type']}) {e['event_text']}  |  entities: {', '.join(e.get('entities', []))}"
             for i, e in enumerate(events_with_ids)]
    events_block = "\n".join(lines)
    prompt = PROMPT_TRENDS.format(n=len(events_with_ids), events_block=events_block)
    result = openai_json(client, prompt, SYSTEM_TRENDS)
    if not isinstance(result, list):
        return []
    return result


# ==============================================
#  STAGE C  –  DISTIL TRENDS INTO THEMES + SECTOR TAGS
# ==============================================

SYSTEM_THEMES = """
You are a senior portfolio strategist AI.
Your job is to synthesise market trends into high-level investment themes
and tag each theme with affected sectors and their sentiment.
Respond ONLY with valid JSON – no preamble, no markdown fences.
""".strip()

PROMPT_THEMES = """
Here are the current market trends:

{trends_block}

Step 1 – Group these trends into broad INVESTMENT THEMES
         (e.g. "AI Revolution", "Energy Transition", "Rate Normalisation").

Step 2 – For each theme, list the equity SECTORS most impacted and assign sentiment.

Return a JSON object with a single key "themes" containing an array:
{{
  "themes": [
    {{
      "theme_name":        "<concise theme name>",
      "theme_description": "<2-3 sentence investor-facing narrative>",
      "trend_indices":     [<0-based indices of trends in this theme>],
      "sector_tags": [
        {{
          "sector": "<sector name, e.g. Semiconductors, Financials, Energy>",
          "sentiment": "<Positive | Negative | Neutral | Mixed>",
          "confidence": <0.0-1.0>,
          "rationale": "<one sentence why>"
        }}
      ]
    }}
  ]
}}
""".strip()


def distil_into_themes(client, trends):
    if not trends:
        return []
    lines = [f"[{i}] ({t.get('direction','?')}) {t['trend_name']}: {t.get('trend_description','')}"
             for i, t in enumerate(trends)]
    trends_block = "\n".join(lines)
    prompt = PROMPT_THEMES.format(trends_block=trends_block)
    result = openai_json(client, prompt, SYSTEM_THEMES)
    if not isinstance(result, list):
        return []
    return result


# ==============================================
#  DB PERSISTENCE
# ==============================================

def persist_market_events(session: Session, article: NewsArticle,
                           raw_events) :
    rows = []
    for ev in raw_events:
        row = MarketEvent(
            article_id  = article.id,
            event_text  = ev.get("event_text", ""),
            event_type  = ev.get("event_type", "OTHER"),
            entities    = json.dumps(ev.get("entities", [])),
        )
        session.add(row)
        rows.append(row)
    session.flush()   # get IDs
    return rows


def get_or_create_trend(session: Session, name: str,
                         description: str, direction: str) -> Trend:
    row = session.query(Trend).filter_by(name=name).first()
    if row:
        row.last_updated  = datetime.utcnow()
        row.description   = description
        return row
    row = Trend(
        name        = name,
        description = description,
        direction   = TrendDirectionEnum(direction) if direction in TrendDirectionEnum._value2member_map_ else TrendDirectionEnum.UNKNOWN,
    )
    session.add(row)
    session.flush()
    return row


def link_events_to_trend(session: Session, trend: Trend,
                          event_rows,
                          indices, scores):
    for idx, score in zip(indices, scores):
        if idx >= len(event_rows):
            continue
        ev = event_rows[idx]
        existing = (session.query(MarketEventTrend)
                    .filter_by(market_event_id=ev.id, trend_id=trend.id)
                    .first())
        if not existing:
            session.add(MarketEventTrend(
                market_event_id = ev.id,
                trend_id        = trend.id,
                relevance_score = float(score),
            ))


def get_or_create_theme(session: Session, name: str, description: str) -> Theme:
    row = session.query(Theme).filter_by(name=name).first()
    if row:
        row.last_updated = datetime.utcnow()
        row.description  = description
        return row
    row = Theme(name=name, description=description)
    session.add(row)
    session.flush()
    return row


def link_trends_to_theme(session: Session, theme: Theme,
                          trend_rows, indices):
    for idx in indices:
        if idx >= len(trend_rows):
            continue
        t = trend_rows[idx]
        existing = (session.query(TrendTheme)
                    .filter_by(trend_id=t.id, theme_id=theme.id)
                    .first())
        if not existing:
            session.add(TrendTheme(trend_id=t.id, theme_id=theme.id))


def add_sector_tags(session: Session, theme: Theme, raw_tags):
    for tag in raw_tags:
        sentiment_val = tag.get("sentiment", "Neutral")
        try:
            sentiment = SentimentEnum(sentiment_val)
        except ValueError:
            sentiment = SentimentEnum.NEUTRAL

        row = SectorTag(
            theme_id    = theme.id,
            sector_name = tag.get("sector", "Unknown"),
            sentiment   = sentiment,
            confidence  = float(tag.get("confidence", 1.0)),
            rationale   = tag.get("rationale", ""),
        )
        session.add(row)


# ==============================================
#  MAIN PROCESSING FUNCTION
# ==============================================

def run_processing(article_ids=None):
    """
    Full Step-2 pipeline.

    Pass article_ids to process specific articles,
    or leave None to process all unprocessed ones.
    """
    log.info("=" * 60)
    log.info("STEP 2 - AI PROCESSING  START")
    log.info("=" * 60)

    engine         = init_db(DATABASE_URL)
    SessionFactory = get_session_factory(engine)
    client         = get_openai_client()

    with SessionFactory() as session:

        # -- fetch articles to process ----------
        q = session.query(NewsArticle).filter_by(is_processed=False)
        if article_ids:
            q = q.filter(NewsArticle.id.in_(article_ids))
        articles = q.limit(MAX_ARTICLES_PER_RUN).all()

        if not articles:
            log.info("No unprocessed articles found – nothing to do.")
            return

        log.info(f"Processing {len(articles)} articles ...")

        # -- collect all events across articles -
        all_event_rows = []
        all_raw_events        = []

        for art in articles:
            log.info(f"\n  Article [{art.id}]: {art.title[:60]}...")

            # STAGE A – extract market events
            try:
                raw_events = extract_market_events(client, art)
            except Exception as e:
                log.error(f"  Event extraction failed: {e}")
                raw_events = []

            log.info(f"  -> {len(raw_events)} market events found")

            event_rows = persist_market_events(session, art, raw_events)
            all_event_rows.extend(event_rows)
            all_raw_events.extend(raw_events)

            art.is_processed = True

        session.flush()

        if not all_raw_events:
            session.commit()
            log.info("No market events extracted.")
            return

        # STAGE B – cluster events into trends
        log.info(f"\n  Clustering {len(all_raw_events)} events into trends ...")
        try:
            raw_trends = cluster_into_trends(client, all_raw_events)
        except Exception as e:
            log.error(f"  Trend clustering failed: {e}")
            raw_trends = []

        log.info(f"  -> {len(raw_trends)} trends identified")

        trend_rows = []
        for rt in raw_trends:
            trend = get_or_create_trend(
                session,
                name        = rt["trend_name"],
                description = rt.get("trend_description", ""),
                direction   = rt.get("direction", "Unknown"),
            )
            link_events_to_trend(
                session, trend, all_event_rows,
                indices = rt.get("event_indices", []),
                scores  = rt.get("relevance_scores", [1.0] * len(rt.get("event_indices", []))),
            )
            trend_rows.append(trend)

        session.flush()

        if not trend_rows:
            session.commit()
            log.info("No trends produced.")
            return

        # STAGE C – distil trends into themes + sector tags
        log.info(f"\n  Distilling {len(trend_rows)} trends into investment themes ...")
        try:
            raw_themes = distil_into_themes(client, raw_trends)
        except Exception as e:
            log.error(f"  Theme distillation failed: {e}")
            raw_themes = []

        log.info(f"  -> {len(raw_themes)} themes identified")

        for rt in raw_themes:
            theme = get_or_create_theme(
                session,
                name        = rt["theme_name"],
                description = rt.get("theme_description", ""),
            )
            link_trends_to_theme(
                session, theme, trend_rows,
                indices = rt.get("trend_indices", []),
            )
            add_sector_tags(session, theme, rt.get("sector_tags", []))

        session.commit()

    # -- print summary --------------------------
    _print_summary(engine)
    log.info("\nSTEP 2 DONE")


def _print_summary(engine):
    """Print a readable summary of what was stored."""
    SessionFactory = get_session_factory(engine)
    with SessionFactory() as session:
        themes = session.query(Theme).all()
        log.info("\n" + "=" * 60)
        log.info(f"  THEMES STORED: {len(themes)}")
        for theme in themes:
            tags = session.query(SectorTag).filter_by(theme_id=theme.id).all()
            log.info(f"\n  > THEME: {theme.name}")
            log.info(f"    {theme.description[:100] if theme.description else ''}")
            for tag in tags:
                log.info(f"    - Sector: {tag.sector_name:30s}  Sentiment: {tag.sentiment.value:10s}  Confidence: {tag.confidence:.2f}")
        log.info("=" * 60)


# ==============================================
#  CLI ENTRY POINT
# ==============================================

if __name__ == "__main__":
    # Process all unprocessed articles in DB
    run_processing()