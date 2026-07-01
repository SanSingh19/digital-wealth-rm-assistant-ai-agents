"""
api.py – Step 4: Read-only REST API over the Finance Pipeline database.

Serves client portfolio overview + matched investment themes for a
mid-tier application to consume. Does NOT trigger scraping, LLM calls,
or matching — it only reads what pipeline.py has already written.


"""

import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from models import (
    init_db, get_session_factory,
    Client, Account, Portfolio, Holding, Security,
    Theme, SectorTag, ClientThemeMatch, NewsArticle, ClientOutlook,
)
from config.settings import DATABASE_URL

log = logging.getLogger("api")

app = FastAPI(
    title="Wealth RM Meeting Preparation API",
    description="Read-only API for client portfolios and matched investment themes.",
    version="1.0.0",
)

# Allow the mid-tier app to call this from a browser/different host
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten this to your mid-tier app's domain in production
    allow_methods=["GET"],
    allow_headers=["*"],
)

_engine = init_db(DATABASE_URL)
_SessionFactory = get_session_factory(_engine)


def get_db():
    """FastAPI dependency: yields a DB session per-request, closes it after."""
    db = _SessionFactory()
    try:
        yield db
    finally:
        db.close()


# ---------- Response schemas ----------

class HoldingOut(BaseModel):
    ticker: str
    security_name: Optional[str]
    sector: Optional[str]
    quantity: float
    avg_cost: Optional[float]
    current_price: Optional[float]
    current_value: Optional[float]
    weight_pct: Optional[float]


class PortfolioOut(BaseModel):
    portfolio_code: str
    name: Optional[str]
    strategy: Optional[str]
    total_value: float
    last_valued_at: Optional[datetime]
    holdings: list[HoldingOut]


class ClientOut(BaseModel):
    client_id: int
    client_code: str
    name: str
    risk_profile: Optional[str]
    portfolios: list[PortfolioOut]


class ThemeMatchOut(BaseModel):
    theme_id: int
    theme_name: str
    matched_sectors: list[str]
    exposure_value: float
    exposure_pct: float
    sentiment: Optional[str]
    confidence: float
    matched_at: Optional[datetime]


class ClientOverviewOut(BaseModel):
    """Combined view: portfolio + matched themes, for a single mid-tier call."""
    client: ClientOut
    matched_themes: list[ThemeMatchOut]


class OutlookDriverOut(BaseModel):
    title: str
    commentary: str


class ClientOutlookOut(BaseModel):
    headline_outlook: str
    drivers: list[OutlookDriverOut]
    generated_at: Optional[datetime]

# ---------- Helpers ----------

def _client_or_404(db: Session, client_id: int) -> Client:
    client = (
        db.query(Client)
        .options(
            joinedload(Client.accounts)
            .joinedload(Account.portfolios)
            .joinedload(Portfolio.holdings)
            .joinedload(Holding.security)
            .joinedload(Security.sector)
        )
        .filter(Client.id == client_id)
        .first()
    )
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client


def _build_client_out(client: Client) -> ClientOut:
    portfolios_out = []
    for account in client.accounts:
        for pf in account.portfolios:
            holdings_out = [
                HoldingOut(
                    ticker=h.security.ticker,
                    security_name=h.security.name,
                    sector=h.security.sector.name if h.security.sector else None,
                    quantity=h.quantity,
                    avg_cost=h.avg_cost,
                    current_price=h.security.last_price,
                    current_value=h.current_value,
                    weight_pct=h.weight_pct,
                )
                for h in pf.holdings
            ]
            portfolios_out.append(PortfolioOut(
                portfolio_code=pf.portfolio_code,
                name=pf.name,
                strategy=pf.strategy,
                total_value=pf.total_value or 0.0,
                last_valued_at=pf.last_valued_at,
                holdings=holdings_out,
            ))

    return ClientOut(
        client_id=client.id,
        client_code=client.client_code,
        name=client.name,
        risk_profile=client.risk_profile,
        portfolios=portfolios_out,
    )


def _build_theme_matches(db: Session, client_id: int) -> list[ThemeMatchOut]:
    matches = (
        db.query(ClientThemeMatch)
        .options(joinedload(ClientThemeMatch.theme))
        .filter(ClientThemeMatch.client_id == client_id)
        .order_by(ClientThemeMatch.exposure_pct.desc())
        .all()
    )
    return [
        ThemeMatchOut(
            theme_id=m.theme_id,
            theme_name=m.theme.name,
            matched_sectors=json.loads(m.matched_sectors or "[]"),
            exposure_value=m.exposure_value,
            exposure_pct=m.exposure_pct,
            sentiment=m.sentiment.value if m.sentiment else None,
            confidence=m.confidence,
            matched_at=m.matched_at,
        )
        for m in matches
    ]


# ---------- Endpoints ----------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/clients", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    """List all clients with their portfolios (no theme matches — use /overview for that)."""
    clients = (
        db.query(Client)
        .options(
            joinedload(Client.accounts)
            .joinedload(Account.portfolios)
            .joinedload(Portfolio.holdings)
            .joinedload(Holding.security)
            .joinedload(Security.sector)
        )
        .all()
    )
    return [_build_client_out(c) for c in clients]


@app.get("/clients/{client_id}/portfolio", response_model=ClientOut)
def get_client_portfolio(client_id: int, db: Session = Depends(get_db)):
    """Client's portfolio holdings only — no theme data."""
    client = _client_or_404(db, client_id)
    return _build_client_out(client)


@app.get("/clients/{client_id}/themes", response_model=list[ThemeMatchOut])
def get_client_themes(client_id: int, db: Session = Depends(get_db)):
    """Matched investment themes for a client only — no portfolio data."""
    _client_or_404(db, client_id)  # 404 check
    return _build_theme_matches(db, client_id)


@app.get("/clients/{client_id}/overview", response_model=ClientOverviewOut)
def get_client_overview(client_id: int, db: Session = Depends(get_db)):
    """
    Combined view for the mid-tier app: portfolio + matched themes
    in a single call. This is the main endpoint the mid-tier app should use.
    """
    client = _client_or_404(db, client_id)
    return ClientOverviewOut(
        client=_build_client_out(client),
        matched_themes=_build_theme_matches(db, client_id),
    )


@app.get("/news/recent")
def get_recent_news(limit: int = 20, db: Session = Depends(get_db)):
    """Recent ingested news articles (raw Step 1 data), for context display."""
    articles = (
        db.query(NewsArticle)
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "title": a.title,
            "url": a.url,
            "published_at": a.published_at,
            "source_name": a.source_name,
            "summary": a.summary,
        }
        for a in articles
    ]

@app.get("/clients/{client_id}/outlook", response_model=ClientOutlookOut)
def get_client_outlook(client_id: int, db: Session = Depends(get_db)):
    """AI-generated market outlook for this client (read-only, pre-computed by step5_advisor.py)."""
    _client_or_404(db, client_id)
    outlook = db.query(ClientOutlook).filter_by(client_id=client_id).first()
    if not outlook:
        raise HTTPException(status_code=404, detail="No outlook generated yet for this client")
    return ClientOutlookOut(
        headline_outlook=outlook.headline_outlook,
        drivers=json.loads(outlook.drivers or "[]"),
        generated_at=outlook.generated_at,
    )