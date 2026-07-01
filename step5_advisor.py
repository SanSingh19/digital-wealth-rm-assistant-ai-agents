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

log = logging.getLogger("step5_advisor")


# ---------- Structured output schema ----------

class OutlookDriver(BaseModel):
    title: str = Field(description="Short headline for this driver, e.g. 'ECB Holds Rates at 2.75%'")
    commentary: str = Field(description="short 1 sentence portfolio-specific commentary on this driver")


class ClientOutlookResult(BaseModel):
    headline_outlook: str = Field(
        description="A 2-3 sentence news summary covering key recent happenings "
                "across the sectors this client is most exposed to. Focus on "
                "what is actually happening in the market, not on portfolio impact."
    )
    drivers: list[OutlookDriver] = Field(
        description="2-3 specific market drivers (news events, theme shifts, rate "
                     "decisions, earnings) each with portfolio-specific commentary."
    )


PARSER = PydanticOutputParser(pydantic_object=ClientOutlookResult)

PROMPT = ChatPromptTemplate.from_template(
    """You are a financial news analyst. Based on the client's sector exposures and 
the recent news provided below, write a concise sector-focused news summary.

For the headline_outlook: summarise what is actually happening in the markets 
across the sectors this client is most heavily invested in. Write it like a 
briefing note — cover key events, moves, and sentiment shifts. Do NOT frame 
it as advice or portfolio impact. Stick strictly to what the news says.

For the drivers: pick 2-3 specific events from the news that are most relevant 
to this client's sector exposure, with one sentence on what happened.

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

MATCHED INVESTMENT THEMES
--------------------------
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
            f"- {m.theme.name}: sentiment={m.sentiment.value if m.sentiment else 'N/A'}, "
            f"exposure={m.exposure_pct:.1f}% (${m.exposure_value:,.0f}), "
            f"via sectors: {', '.join(sectors)}"
        )

    news_lines = []
    for article in news:
        news_lines.append(f"- {article.title}: {article.summary or ''}".strip())

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
    reverse=True)[:3]

    theme_ids = [m.theme_id for m in top_matches]

    if not theme_ids:
        return []

    articles = (
        session.query(NewsArticle)
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

    return articles


def run_advisor(client_ids: list[int] | None = None) -> dict:
    """Generate and save market outlooks for all (or specified) clients."""
    engine = init_db(DATABASE_URL)
    Session = get_session_factory(engine)

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3, api_key=OPENAI_API_KEY)
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
            news = _relevant_news_for_client(session, matches)

            context = _build_context(client, matches, news)

            try:
                result: ClientOutlookResult = chain.invoke(context)
            except Exception as e:
                log.error(f"  [{client.client_code}] LLM call failed: {e}")
                continue

            existing = session.query(ClientOutlook).filter_by(client_id=client.id).first()
            drivers_json = json.dumps([d.model_dump() for d in result.drivers])

            if existing:
                existing.headline_outlook = result.headline_outlook
                existing.drivers = drivers_json
                existing.generated_at = datetime.utcnow()
            else:
                session.add(ClientOutlook(
                    client_id=client.id,
                    headline_outlook=result.headline_outlook,
                    drivers=drivers_json,
                ))

            session.commit()
            results[client.id] = result.headline_outlook
            log.info(f"  [{client.client_code}] outlook generated "
                      f"({len(result.drivers)} drivers).")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_advisor()