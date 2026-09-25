"""
step5_advisor.py – Step 5: AI advisor agent.

For each client, builds context from their portfolio + matched themes +
recent relevant news, sends it to GPT-4o via LangChain, and saves a
structured market outlook (headline + per-driver commentary) to the DB.

This is the ONLY step that calls the LLM here — api.py just reads results.
"""

import json
import logging
from datetime import datetime
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from sqlalchemy.orm import joinedload

from models import (
    init_db, get_session_factory,
    Client, Account, Portfolio, Holding, Security,
    Theme, SectorTag, ClientThemeMatch, NewsArticle, MarketEvent,MarketEventTrend,
    Trend,
    TrendTheme,
    ClientOutlook,
)
from config.settings import DATABASE_URL, OPENAI_API_KEY

import ssl
import certifi
import os

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

log = logging.getLogger("step5_advisor")


# ---------- Structured output schema ----------

class OutlookDriver(BaseModel):
    title: str = Field(description="Short headline for this driver, e.g. 'ECB Holds Rates at 2.75%'")
    commentary: str = Field(description="short 1 sentence portfolio-specific commentary on this driver")
    status: Literal["Increase", "Decrease"] = Field(
        description="Indicates whether this market event is positively increasing, "
                    "negatively decreasing impact on the client's portfolio value or exposure."
    )
    client_match_theme_id: int = Field(
            description="The exact ClientThemeMatch.id of the matched investment theme "
                        "that this driver was generated from."
        )


class ClientOutlookResult(BaseModel):
    headline_outlook: str = Field(
        description="A 2-3 sentence news summary covering key recent happenings "
                    "across the sectors this client is most exposed to. Focus on "
                    "what is actually happening in the market, not on portfolio impact."
    )
    drivers: list[OutlookDriver] = Field(
        description="2-3 specific market drivers (news events, theme shifts, rate "
                    "decisions, earnings) each with portfolio-specific commentary "
                    "and a status indicating Increase, Decrease impact "
                    "on the client's portfolio."
    )


PARSER = PydanticOutputParser(pydantic_object=ClientOutlookResult)

PROMPT = ChatPromptTemplate.from_template(
    """You are a financial news analyst. Based on the client's sector exposures and
the recent news provided below, write a concise sector-focused news summary.

Use only the provided portfolio holdings, top 3 matched investment themes,
and recent market news as the evidence for this outlook.
Do not introduce or infer additional client themes that are not provided.

For the headline_outlook: summarise only what is explicitly supported by
the RECENT MARKET NEWS & EVENTS provided below.

Do not generalize a specific news event into a broader sector trend,
industry trend, technology trend, market trend, or economic trend unless
that broader trend is explicitly stated or clearly supported by the
provided news.

Do not describe an event as being part of a sector or industry unless
the provided news explicitly identifies that sector or industry.

Do not use words such as "significant", "major trend", "ongoing trend",
"growing trend", "increasing trend", or similar broad characterizations
unless the provided news explicitly supports them.

Use the client's portfolio holdings and sectors ONLY to determine which
news is relevant to the client.
Do NOT introduce a portfolio company, security, sector, product, or industry
into the headline_outlook merely because it appears in the portfolio.
A portfolio sector is NOT evidence that a news event affected that sector.
A company, security, product, or event mentioned in the news does not by
itself establish that the news relates to a particular sector.

Do not map a company to a sector using outside knowledge. Use a sector
connection only when the sector is explicitly stated in the provided news
or when the provided news directly describes an activity that is explicitly
identified with that sector in the supplied context.

If the sector connection cannot be established from the supplied evidence,
do not mention that sector in the headline or driver.
If the provided news does not contain a development related to a client's
sector, do not manufacture a sector-specific connection. Summarise only
the market developments actually present in the news.

Write it like a concise factual briefing note covering only the key events
and market movements explicitly stated in the provided news.

Do not add interpretation, causality, sentiment, significance, or broader
market conclusions unless they are explicitly stated in the provided news.

Do NOT frame it as advice or portfolio impact.

For the drivers: select up to 3 specific events from the provided news
that have an explicitly supported connection to the client's matched
sectors.

Do not force the output to contain 2-3 drivers.

If only 1 event is sufficiently supported, return 1 driver.
If no event is sufficiently supported, return an empty drivers array.

Never create a driver merely to satisfy the requested number of drivers.

IMPORTANT DRIVER GROUNDING RULES:
- The driver title must describe the underlying market development using
  facts explicitly supported by the provided news.
- Do not copy the article title verbatim or near-verbatim.
- Do not simply replace or rearrange words from the article title.
- The driver title should identify the actual development, such as a rate
  decision, regulatory action, acquisition approval, earnings result, policy
  change, or market movement, only when that development is explicitly
  supported by the provided evidence.
- Do not add a sector, industry, company impact, or broader market trend to
  the driver title unless it is explicitly supported by the provided news.
- The driver title and commentary must be based only on facts explicitly
  stated in the provided news.
- Do not introduce any company, security, sector, product, customer,
  competitor, beneficiary, or business relationship that is not explicitly
  mentioned in the provided news or portfolio holdings.
- Do not assume that a company benefits from or is affected by a news event
  unless the provided news explicitly supports that relationship.
- Do not use outside knowledge or general knowledge about the sector to fill
  missing information.
- Every factual statement in the driver commentary must be directly
  supported by the provided news.
- If the news does not provide enough evidence to create a specific driver,
  omit that driver rather than guessing or generating unsupported information.
- The news article title is only the source title. Do not automatically use
  the article title as the driver title.

For example:
News article:
"Air Products Is Doubling Down on the Gases Inside Chip Fabs"
Driver title:
"Semiconductor fab investment is expanding"
Do NOT create unsupported statements such as:
"This benefits NVIDIA and ASML."
unless NVIDIA and ASML and that relationship are explicitly supported by
the provided news.

SECTOR SCOPING RULE:

For each matched investment theme, use ONLY the sectors listed in that client's
matched_sectors value.

A theme may affect multiple sectors globally, but that does NOT mean every
sector under that theme belongs to this client.

A news article/event is relevant to the client only when its actual content
supports a connection to one of the client's matched sectors.

Do NOT infer sector relevance merely because:
• the article belongs to a matched theme
• the company mentioned in the article belongs to another sector
• the theme has that sector globally
• the portfolio contains a related theme

The provided news context includes the client's matched sectors,
trend, market event, and article information.

For each news item, first determine whether the Trend, Market Event,
or News Article content is actually relevant to one of the client's
matched sectors.

Focus only on sector-relevant information supported by that content.
If a news item does not contain enough evidence connecting it to the
client's matched sector, ignore it.

Do not assume that every news item under a matched theme is relevant
to every sector within that theme.

The matched sector list is a relevance filter, not evidence.

A news item must contain explicit evidence connecting the event to the
specific matched sector.

Do not use the theme name, trend name, company name, or portfolio holding
alone to establish that connection.

If the connection requires outside knowledge or an unstated assumption,
treat the news item as not sufficiently supported and omit it.

If the supplied evidence does not establish that the news/event relates to
the client's matched sector, DO NOT use that article as a market driver.

When sector relevance cannot be established from the supplied evidence, omit the driver rather than guessing.

DRIVER THEME SOURCE RULE:

For every driver, you MUST set client_match_theme_id to the exact
ClientThemeMatch ID of the matched investment theme that the driver
was generated from.

The client_match_theme_id must be the exact ClientThemeMatch ID attached
to the RECENT MARKET NEWS & EVENTS evidence used to generate that driver.

Copy the ID exactly as supplied.

Do not determine the ID by comparing theme names or sector names.
Do not invent, modify, calculate, or infer an ID.

If the evidence used to create a driver cannot be tied to exactly one
supplied ClientThemeMatch ID, omit that driver.

Each driver must have exactly one client_match_theme_id.

Do not invent, modify, or reuse an ID that is not provided.

The selected theme must be the specific theme whose affected sectors
and provided evidence support the driver.

For each driver status field: set "Increase" if the provided news explicitly supports a positive impact on the client's holdings
or sector exposure, and "Decrease" if the provided news explicitly supports a negative impact.
Do not infer the impact from general market knowledge or assumptions.
If the direction of impact is not explicitly supported by the provided news,
do not invent a directional claim.

The headline_outlook must also follow strict evidence grounding:
- For headline_outlook, mention only companies, sectors, products, events,
  numbers, and relationships explicitly present in the provided news.
- Portfolio holdings and sectors are used only to determine relevance.
- Do not introduce portfolio companies or sectors into the headline_outlook
  unless they are explicitly mentioned in the provided news.
- Do not introduce companies merely because they are generally associated
  with the mentioned sector.
- Do not infer that a company benefits from, depends on, competes with,
  supplies, or is affected by an event unless the provided evidence explicitly
  states that relationship.
- If a fact is not supported by the provided evidence, leave it out.
STRICT EVIDENCE RULE:

Treat the provided news as the complete evidence set.

Do not convert facts into broader interpretations.

For example:
- "Company A settled a lawsuit" does not mean the company won a major
  legal victory unless the provided news explicitly says so.
- "Company A announced an acquisition" does not mean the acquisition is
  beneficial to the market or represents an industry trend.
- "The dollar rose" does not mean investors are concerned about inflation
  unless the provided news explicitly states that.
- A company's presence in the portfolio does not mean the company was
  affected by the news.
- A matched theme does not prove that a news event is relevant to every
  sector under that theme.

When a statement requires an inference beyond the provided evidence,
remove that statement.

Prefer a narrower factual statement over a broader interpretation.

CLIENT SECTOR EXPOSURE
-----------------------
Name: {client_name}
Top sectors by investment weight: (derived from holdings below)

PORTFOLIO HOLDINGS
------------------
{holdings_text}

RECENT MARKET NEWS & EVENTS
-----------------------------
{news_text}

MATCHED INVESTMENT THEMES – TOP 3 BY EXPOSURE
----------------------------------------------
{themes_text}

{format_instructions}
"""
)


def _build_context(client: Client, matches: list[ClientThemeMatch], news: list) -> dict:
    holdings_lines = []
    for account in client.accounts:
        for pf in account.portfolios:
            for h in pf.holdings:
                sec = h.security
                sector = sec.sector.name if sec.sector else "Unknown"
                holdings_lines.append(
                    f"- {sec.ticker} ({sec.name}), sector={sector}, "
                    f"value=${h.current_value:,.0f} ({h.weight_pct:.1f}% of portfolio)"
                )

    theme_lines = []
    for m in matches:
        sectors = json.loads(m.matched_sectors or "[]")
        theme_lines.append(
            f"- ClientThemeMatch ID: {m.id}\n"
            f"  Theme: {m.theme.name}\n"
            f"  Sentiment: {m.sentiment.value if m.sentiment else 'N/A'}\n"
            f"  Exposure: {m.exposure_pct:.1f}% (${m.exposure_value:,.0f})\n"
            f"  Affected sectors: {', '.join(sectors)}"
        )

    news_lines = []

    for article, market_event, trend, theme_id in news:

        match = next(
            (m for m in matches if m.theme_id == theme_id),
            None
        )

        if not match:
            continue

        sectors = json.loads(match.matched_sectors or "[]")

        news_lines.append(
            f"- ClientThemeMatch ID: {match.id}\n"
            f"  Theme: {match.theme.name}\n"
            f"  Client matched sectors for this theme: {', '.join(sectors)}\n"
            f"  Trend: {trend.name}\n"
            f"  Market Event: {market_event.event_text}\n"
            f"  News Article: {article.title}\n"
            f"  Summary: {article.summary or ''}"
        )

    return {
        "client_name": client.name,
        "risk_profile": client.risk_profile or "Not specified",
        "holdings_text": "\n".join(holdings_lines) or "No holdings on file.",
        "themes_text": "\n".join(theme_lines) or "No matched themes.",
        "news_text": "\n".join(news_lines) or "No recent relevant news.",
        "format_instructions": PARSER.get_format_instructions(),
    }


def _relevant_news_for_client(
    session,
    matches: list[ClientThemeMatch],
    limit: int = 5
) -> list:

    top_matches = sorted(
        matches,
        key=lambda x: x.exposure_pct,
        reverse=True
    )[:3]

    if not top_matches:
        return []

    theme_ids = [m.theme_id for m in top_matches]

    rows = (
        session.query(
            NewsArticle,
            MarketEvent,
            Trend,
            TrendTheme.theme_id
        )
        .join(
            MarketEvent,
            MarketEvent.article_id == NewsArticle.id
        )
        .join(
            MarketEventTrend,
            MarketEventTrend.market_event_id == MarketEvent.id
        )
        .join(
            Trend,
            Trend.id == MarketEventTrend.trend_id
        )
        .join(
            TrendTheme,
            TrendTheme.trend_id == Trend.id
        )
        .filter(
            TrendTheme.theme_id.in_(theme_ids)
        )
        .order_by(
            NewsArticle.published_at.desc()
        )
        .distinct()
        .limit(limit)
        .all()
    )

    return rows


def _build_citation(
    matches: list[ClientThemeMatch],
    news: list,
) -> str:
    """
    Build citation directly from the exact news context passed to the LLM.

    Hierarchy:
        Theme
            -> Trend
                -> News Article
                    -> Market Events
    """

    citations = {
        "themes": []
    }

    if not news:
        return json.dumps(citations)

    theme_lookup = {}

    for article, market_event, trend, theme_id in news:

        match = next(
            (m for m in matches if m.theme_id == theme_id),
            None
        )

        if not match:
            continue

        # ---------------------------------------------------------
        # Theme
        # ---------------------------------------------------------
        if theme_id not in theme_lookup:

            theme_entry = {
                "theme": match.theme.name,
                "trends": []
            }

            citations["themes"].append(theme_entry)

            theme_lookup[theme_id] = {
                "entry": theme_entry,
                "trends": {}
            }

        theme_data = theme_lookup[theme_id]

        # ---------------------------------------------------------
        # Trend
        # ---------------------------------------------------------
        if trend.id not in theme_data["trends"]:

            trend_entry = {
                "trend": trend.name,
                "news_articles": []
            }

            theme_data["entry"]["trends"].append(trend_entry)

            theme_data["trends"][trend.id] = {
                "entry": trend_entry,
                "articles": {}
            }

        trend_data = theme_data["trends"][trend.id]

        # ---------------------------------------------------------
        # News Article
        # ---------------------------------------------------------
        if article.id not in trend_data["articles"]:

            article_entry = {
                "title": article.title,
                "url": article.url,
                "market_events": []
            }

            trend_data["entry"]["news_articles"].append(article_entry)

            trend_data["articles"][article.id] = {
                "entry": article_entry,
                "events": set()
            }

        article_data = trend_data["articles"][article.id]

        # ---------------------------------------------------------
        # Market Event
        # ---------------------------------------------------------
        if market_event.id not in article_data["events"]:

            article_data["entry"]["market_events"].append(
                market_event.event_text
            )

            article_data["events"].add(market_event.id)

    return json.dumps(citations)

def run_advisor(client_ids: list[int] | None = None) -> dict:
    """Generate and save market outlooks for all (or specified) clients."""
    engine = init_db(DATABASE_URL)
    Session = get_session_factory(engine)

    import httpx

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=OPENAI_API_KEY,
        http_client=httpx.Client(verify=False)
    )
    chain = PROMPT | llm | PARSER

    results = {}
    with Session() as session:
        client_query = session.query(Client).options(
            joinedload(Client.accounts)
            .joinedload(Account.portfolios)
            .joinedload(Portfolio.holdings)
            .joinedload(Holding.security)
            .joinedload(Security.sector)
        )
        if client_ids:
            client_query = client_query.filter(Client.id.in_(client_ids))
        clients = client_query.all()

        if not clients:
            log.warning("No clients found.")
            return {}

        for client in clients:
            matches = (
                session.query(ClientThemeMatch)
                .options(joinedload(ClientThemeMatch.theme))
                .filter(ClientThemeMatch.client_id == client.id)
                .order_by(ClientThemeMatch.exposure_pct.desc())
                .all()
            )
            # Use the same top 3 themes for both:
            # 1. relevant news selection
            # 2. LLM context
            top_matches = matches[:3]
            news = _relevant_news_for_client(session, top_matches)

            context = _build_context(client, top_matches, news)
            citation_json = _build_citation(top_matches, news)

            try:
                result: ClientOutlookResult = chain.invoke(context)
            except Exception as e:
                log.exception(f"  [{client.client_code}] LLM call failed")
                continue
            # ==========================================================
            # Validate driver -> ClientThemeMatch relationship
            # ==========================================================

            # These are the Theme IDs that actually have news evidence
            # supplied to GPT.
            news_theme_ids = {
                theme_id
                for _, _, _, theme_id in news
            }

            # Convert the Theme IDs into this client's valid
            # ClientThemeMatch IDs.
            valid_client_match_ids = {
                match.id
                for match in top_matches
                if match.theme_id in news_theme_ids
            }
            log.info(
                "[%s] Valid ClientThemeMatch IDs for outlook drivers: %s",
                client.client_code,
                sorted(valid_client_match_ids),
            )

            valid_drivers = []

            for driver in result.drivers:

                if driver.client_match_theme_id not in valid_client_match_ids:

                    log.warning(
                        "[%s] Removing driver '%s': "
                        "invalid client_match_theme_id=%s",
                        client.client_code,
                        driver.title,
                        driver.client_match_theme_id,
                    )

                    continue

                valid_drivers.append(driver)

            # Replace GPT output with only validated drivers.
            result.drivers = valid_drivers


            # ==========================================================
            # Save ClientOutlook
            # ==========================================================

            existing = session.query(ClientOutlook).filter_by(client_id=client.id).first()
            drivers_json = json.dumps([d.model_dump() for d in result.drivers])

            if existing:
                existing.headline_outlook = result.headline_outlook
                existing.drivers = drivers_json
                existing.citation = citation_json
                existing.generated_at = datetime.utcnow()
            else:
                session.add(ClientOutlook(
                    client_id=client.id,
                    headline_outlook=result.headline_outlook,
                    drivers=drivers_json,
                    citation=citation_json,
                ))

            session.commit()
            results[client.id] = result.headline_outlook
            log.info(f"  [{client.client_code}] outlook generated "
                      f"({len(result.drivers)} drivers).")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_advisor()