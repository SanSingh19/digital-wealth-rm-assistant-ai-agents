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
from pathlib import Path
import json

from openai import OpenAI
from sqlalchemy.orm import Session

import httpx
from openai import OpenAI

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
    return OpenAI(
    api_key=api_key,
    http_client=httpx.Client(verify=False)
    )


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
    prompt = PROMPT_MARKET_EVENTS.format(
        title=article.title,
        summary=article.summary or "",
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

Your job is to classify market trends into investment themes.

The existing investment themes provided in the user prompt come
directly from the Theme database table.

For EVERY trend, follow this decision process in this exact order:

STEP 1 — CHECK EXISTING DATABASE THEMES
---------------------------------------

Compare the trend against ALL existing investment themes provided
in the prompt.

Evaluate the underlying investment meaning using:
- trend_name
- trend_description
- direction
- theme_name
- category
- description
- classification_guidance

The comparison must be semantic and based on investment context.

Do NOT use simple keyword matching.

Do NOT require exact wording.

A trend can match an existing theme even when the wording is
different, as long as the underlying investment narrative is
genuinely the same.

STEP 2 — USE EXISTING DATABASE THEME
------------------------------------

If an existing theme genuinely represents the primary investment
narrative of the trend:

- MUST use that existing theme.
- MUST NOT create a new theme.
- theme_id MUST be the exact database Theme.id.
- theme_name MUST exactly match the database theme name.
- theme_description MUST use the existing database description.

STEP 3 — GENERATE A NEW THEME ONLY WHEN NECESSARY
--------------------------------------------------

If NONE of the existing database themes genuinely represents
the underlying investment narrative:

- Create a new theme.
- theme_id MUST be null.
- The generated theme must be meaningful and reusable.
- It must describe a broader investment narrative.
- It must NOT be a company name.
- It must NOT be a news headline.
- It must NOT be a temporary event.
- It must NOT simply reword an existing database theme.

IMPORTANT MATCHING RULES
------------------------

1. Match based on investment meaning, not word overlap.

2. Do not map a trend to a theme only because one word appears
   in both.

3. When multiple existing themes are related, select the theme
   representing the PRIMARY investment narrative.

4. Multiple trends may map to the same theme.

5. A trend may map to multiple themes only when it genuinely
   contains multiple distinct investment narratives.

6. Do not force a trend into an unrelated existing theme merely
   to avoid creating a new theme.

7. New themes are allowed only after ALL existing database themes
   have been considered and none is a genuine match.

SECTOR TAGGING
--------------

For every resulting theme, identify the affected equity sectors
and assign sentiment.

Do not invent sectors simply to create a client match.

Return ONLY valid JSON.
""".strip()

PROMPT_THEMES = """
CURRENT MARKET TRENDS
=====================

{trends_block}


EXISTING INVESTMENT THEMES FROM DATABASE
============================

{themes_block}


TASK
====

For EACH market trend, perform the following steps IN ORDER:

STEP 1:
Compare the trend against ALL EXISTING INVESTMENT THEMES FROM DATABASE.

STEP 2:
If a existing database theme is a genuine semantic match for the trend's
primary investment narrative, use that existing database theme.

STEP 3:
Only if NO existing database theme is a genuine match, create a new
GENERATED investment theme.

NEVER generate a new theme when an existing database theme is a
genuine match.

NEVER force a trend into an unrelated existing database theme merely to avoid
generating a new theme.


MATCHING REQUIREMENT
====================

You MUST evaluate the existing database themes FIRST.

The matching must be SEMANTIC.

Compare the underlying investment meaning of the trend with:

- theme_name
- category
- description
- classification_guidance

Do NOT use simple keyword matching.

An exact word or phrase match is NOT required.

A trend can match a existing database theme even when the wording is
different, if the underlying investment concept is genuinely the same.

A trend must NOT match a existing database theme only because a word
happens to appear in both the trend and the theme.

When multiple themes are related, identify the PRIMARY investment
narrative of the trend and select the existing database theme that best
represents that narrative.

Only generate a new theme when NONE of the existing database themes
genuinely represent the trend's underlying investment concept.

The examples below illustrate how to reason about semantic matching.
They are NOT hardcoded mappings. Always compare against the actual
database themes provided above and use an existing theme only when
its actual database description and classification guidance support
the match.

IMPORTANT EXAMPLES
==================

Example 1:
Trend:
"GPU demand is accelerating as AI server deployments increase."
Evaluate the trend based on its underlying investment narrative.
If the primary narrative is semiconductor / GPU / AI accelerator /
advanced-computing demand, it should map to:
"Artificial Intelligence, Automation & Advanced Computing"
Do not select a theme merely because of the word "AI".


Example 2:
Trend:
"Hyperscalers are increasing capital expenditure on data-center
capacity and cloud infrastructure."
This should be evaluated primarily as a digital infrastructure /
cloud investment narrative and should map to:
"Digital Infrastructure & Cloud"


Example 3:
Trend: "Central banks are maintaining restrictive monetary policy."
This should be evaluated as a monetary-policy / interest-rate
investment narrative and should map to:
"Monetary Policy & Interest Rate Cycle"


Example 4:
Trend:
"Manufacturers are moving production closer to domestic markets
to reduce dependence on overseas suppliers."
This should be evaluated as a supply-chain restructuring /
reshoring narrative and should map to:
"Supply Chain Resilience & Reshoring"

Example 5:
If a trend does not genuinely fit ANY existing database theme, create a
new theme rather than forcing the trend into an unrelated
existing database theme.

Example 6:
Trend:
"Commercial space infrastructure investment is accelerating through
launch capacity, satellite infrastructure and private-space
deployment."
If none of the existing database themes genuinely represents this
investment narrative, generate:
theme_id: null
theme_name: "Commercial Space Infrastructure"
theme_description: "<description of the investment narrative>"


OUTPUT FORMAT
=============

Return a JSON object with exactly one key: "themes".

{{
  "themes": [
    {{
      "theme_id": <existing database Theme.id OR null>,
      "theme_name": "<exact existing theme name OR generated theme name>",
      "theme_description": "<existing description OR generated description>",
      "category": "<existing database category OR generated category>",
      "classification_guidance": "<existing database guidance OR generated guidance>",
      "trend_indices": [<0-based trend indices>],
      "match_reason": "<short explanation of why the trend meaning matches this theme>",
      "sector_tags": [
        {{
          "sector": "<sector name>",
          "sentiment": "<Positive | Negative | Neutral | Mixed>",
          "confidence": <0.0-1.0>,
          "rationale": "<one sentence why>"
        }}
      ]
    }}
  ]
}}

FOR EXISTING DATABASE THEMES
============================
When using an existing database theme:
- theme_id MUST exactly match the Theme ID provided in the database theme list.
- theme_name MUST exactly match the existing database theme name.
- theme_description MUST use the existing database theme description.
- category MUST exactly match the existing database theme category.
- classification_guidance MUST exactly match the existing database classification guidance.
- Do not modify or rename the existing database theme.

FOR GENERATED THEMES
===================

When generating a new theme:
- theme_id MUST be null.
- theme_name must be a meaningful new investment theme.
- theme_description must describe the new investment narrative.
- category must be a meaningful broad investment category.
- classification_guidance must explain when this theme should be used for future trend classification.
- Do not create a theme that is simply a rewording of an existing database theme.

""".strip()

def distil_into_themes(client, trends, existing_themes):
    if not trends:
        return []

    # -----------------------------
    # Build trends block
    # -----------------------------
    trend_lines = [
        f"[{i}] ({t.get('direction', '?')}) "
        f"{t['trend_name']}: "
        f"{t.get('trend_description', '')}"
        for i, t in enumerate(trends)
    ]

    trends_block = "\n".join(trend_lines)

    # -----------------------------
    # Build predefined themes block
    # -----------------------------
    theme_lines = []

    for theme in existing_themes:
        theme_lines.append(
            f"[Theme ID: {theme.get('theme_id')}] "
            f"{theme.get('theme_name', '')}\n"
            f"Category: {theme.get('category', '')}\n"
            f"Description: {theme.get('description', '')}\n"
            f"Classification guidance: "
            f"{theme.get('classification_guidance', '')}"
        )

    themes_block = "\n\n".join(theme_lines)

    # -----------------------------
    # Build prompt
    # -----------------------------
    prompt = PROMPT_THEMES.format(
        trends_block=trends_block,
        themes_block=themes_block,
    )

    # -----------------------------
    # Call LLM
    # -----------------------------
    result = openai_json(
        client,
        prompt,
        SYSTEM_THEMES
    )

    if not isinstance(result, list):
        return []

    valid_themes = []
    classified_indices = set()

    for theme in result:
        if not isinstance(theme, dict):
            continue

        indices = theme.get("trend_indices", [])

        if not isinstance(indices, list):
            indices = []

        valid_indices = [
            idx for idx in indices
            if isinstance(idx, int)
            and 0 <= idx < len(trends)
        ]

        theme["trend_indices"] = valid_indices

        for idx in valid_indices:
            classified_indices.add(idx)

        valid_themes.append(theme)

    # Log trends that were not assigned to any theme
    unclassified_indices = set(range(len(trends))) - classified_indices

    if unclassified_indices:
        log.warning(
            f"  Unclassified trend indices from Stage C: "
            f"{sorted(unclassified_indices)}"
        )

    return valid_themes


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

def get_existing_themes(session: Session):
    """
    Load all existing themes from the Theme database table.

    These themes are provided to the LLM during Stage C.
    """

    themes = (
        session.query(Theme)
        .order_by(Theme.id)
        .all()
    )

    return [
        {
            "theme_id": theme.id,
            "theme_name": theme.name,
            "category": theme.category or "",
            "description": theme.description or "",
            "classification_guidance": (
                theme.classification_guidance or ""
            ),
        }
        for theme in themes
    ]

def get_or_create_theme(
    session: Session,
    name: str,
    description: str,
    category: str = "",
    classification_guidance: str = "",
) -> Theme:

    row = session.query(Theme).filter_by(name=name).first()

    if row:
        row.last_updated = datetime.utcnow()
        row.description = description
        row.category = category
        row.classification_guidance = classification_guidance
        return row

    row = Theme(
        name=name,
        category=category,
        description=description,
        classification_guidance=classification_guidance,
    )

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
            existing_themes = get_existing_themes(session)

            log.info(
                f"  -> Loaded {len(existing_themes)} existing investment "
                f"themes from database"
            )

            raw_themes = distil_into_themes(
                client,
                raw_trends,
                existing_themes,
            )

        except Exception as e:
            log.error(f"  Theme distillation failed: {e}")
            raw_themes = []

        log.info(f"  -> {len(raw_themes)} themes identified")

        for rt in raw_themes:

            theme_id = rt.get("theme_id")

            # --------------------------------------
            # EXISTING DATABASE THEME
            # --------------------------------------

            if theme_id is not None:

                theme = (
                    session.query(Theme)
                    .filter_by(id=theme_id)
                    .first()
                )

                if not theme:
                    log.warning(
                        f"  AI returned Theme ID {theme_id}, "
                        f"but it does not exist in the database. "
                        f"Skipping."
                    )
                    continue

                if rt.get("theme_name") != theme.name:
                    log.warning(
                        f"  AI returned Theme ID {theme_id} "
                        f"with mismatched theme name "
                        f"'{rt.get('theme_name')}'. "
                        f"Expected '{theme.name}'. Skipping."
                    )
                    continue

            # --------------------------------------
            # NEW GENERATED THEME
            # --------------------------------------

            else:

                theme = get_or_create_theme(
                    session,
                    name=rt["theme_name"],
                    description=rt.get("theme_description", ""),
                    category=rt.get("category", ""),
                    classification_guidance=rt.get("classification_guidance", ""),
                )

            # --------------------------------------
            # TREND -> THEME
            # --------------------------------------

            link_trends_to_theme(
                session,
                theme,
                trend_rows,
                indices=rt.get("trend_indices", []),
            )

            # --------------------------------------
            # THEME -> SECTOR TAG
            # --------------------------------------

            add_sector_tags(
                session,
                theme,
                rt.get("sector_tags", []),
            )

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