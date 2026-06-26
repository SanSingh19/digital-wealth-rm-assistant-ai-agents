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
    Theme, SectorTag, ClientThemeMatch, NewsArticle, MarketEvent,
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
        description="A single contextual paragraph summarizing the market outlook "
                     "for this specific client, referencing their actual holdings, "
                     "sectors, and themes by name."
    )
    drivers: list[OutlookDriver] = Field(
        description="2-3 specific market drivers (news events, theme shifts, rate "
                     "decisions, earnings) each with portfolio-specific commentary."
    )


PARSER = PydanticOutputParser(pydantic_object=ClientOutlookResult)

PROMPT = ChatPromptTemplate.from_template(
    """You are a wealth management advisor assistant. Write a market outlook for
this specific client based ONLY on the data provided below. Be concrete and
reference actual holdings, sectors, tickers, and theme names. Do not invent
data not present in the context.

CLIENT
------
Name: {client_name}
Risk profile: {risk_profile}

PORTFOLIO HOLDINGS
------------------
{holdings_text}

MATCHED INVESTMENT THEMES
--------------------------
{themes_text}

RECENT RELEVANT NEWS / MARKET EVENTS
--------------------------------------
{news_text}

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


def _relevant_news_for_client(session, matches: list[ClientThemeMatch], limit: int = 8) -> list:
    """Pull recent news articles whose extracted themes overlap this client's matched themes."""
    theme_ids = [m.theme_id for m in matches]
    if not theme_ids:
        return []
    articles = (
        session.query(NewsArticle)
        .join(MarketEvent, MarketEvent.article_id == NewsArticle.id)
        .order_by(NewsArticle.published_at.desc())
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