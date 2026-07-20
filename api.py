"""
api.py – Read-only REST API over the Finance Pipeline database.

Serves client portfolio, themes, outlook, fund recommendations,
talking points, transactions, price history, and meeting data.

Does NOT trigger scraping, LLM calls, or matching — reads pipeline output only.
"""

import json
import logging
from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from models import (
    init_db, get_session_factory,
    Client, Account, Portfolio, Holding, Security,
    Theme, SectorTag, ClientThemeMatch, NewsArticle,
    ClientOutlook, ClientFundRecommendation,
    ClientPersonalDetails, ClientRiskOverview, ClientPreference,
    Meeting, ClientMeetingSummary, ClientAITalkingPoints,
    RelationshipManager, Transaction, SecurityPriceHistory,
)
from config.settings import DATABASE_URL

log = logging.getLogger("api")

app = FastAPI(
    title       = "Wealth RM Meeting Preparation API",
    description = "Read-only API for client portfolios, themes, outlooks and fund recommendations.",
    version     = "2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["GET"],
    allow_headers  = ["*"],
)

_engine         = init_db(DATABASE_URL)
_SessionFactory = get_session_factory(_engine)


def get_db():
    db = _SessionFactory()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════
#  RESPONSE SCHEMAS
# ═══════════════════════════════════════════════

class HoldingOut(BaseModel):
    ticker:        str
    security_name: Optional[str]
    sector:        Optional[str]
    security_type: Optional[str]
    quantity:      float
    avg_cost:      Optional[float]
    current_price: Optional[float]
    current_value: Optional[float]
    weight_pct:    Optional[float]
    pnl:           Optional[float]


class PortfolioOut(BaseModel):
    portfolio_code: str
    name:           Optional[str]
    strategy:       Optional[str]
    total_value:    float
    last_valued_at: Optional[datetime]
    holdings:       list[HoldingOut]


class PersonalDetailsOut(BaseModel):
    marital_status:     Optional[str]
    kids_details:       Optional[str]
    date_of_Birth:      Optional[str]
    hobbies:            Optional[str]
    other:              Optional[str]
    client_constraints: Optional[str]


class RiskOverviewOut(BaseModel):
    concentration_pct:   Optional[str]
    concentration_asset: Optional[str]
    sharpe_ratio:        Optional[str]
    value_at_risk:       Optional[str]
    max_drawdown:        Optional[str]


class PreferenceOut(BaseModel):
    security_type: str
    bandwidth_min: Optional[float]
    bandwidth_max: Optional[float]


class MeetingOut(BaseModel):
    title:    Optional[str]
    date:     Optional[date]
    location: Optional[str]
    platform: Optional[str]


class MeetingSummaryOut(BaseModel):
    main_discussion_points: Optional[list]
    client_questions:       Optional[list]
    last_meeting_date:      Optional[date]


class TransactionOut(BaseModel):
    transaction_type: str
    ticker:           str
    product_name:     str
    amount:           float
    currency:         str
    transaction_date: date


class PriceHistoryOut(BaseModel):
    ticker: str
    month:  str
    year:   int
    price:  Optional[float]


class ClientOut(BaseModel):
    client_id:        int
    client_code:      str
    name:             str
    risk_profile:     Optional[str]
    age:              Optional[int]
    profession:       Optional[str]
    preference:       Optional[str]
    service_model:    Optional[str]
    investment_goals: Optional[str]
    portfolios:       list[PortfolioOut]


class ThemeMatchOut(BaseModel):
    theme_id:        int
    theme_name:      str
    matched_sectors: list[str]
    exposure_value:  float
    exposure_pct:    float
    sentiment:       Optional[str]
    confidence:      float
    matched_at:      Optional[datetime]


class ClientOverviewOut(BaseModel):
    client:         ClientOut
    matched_themes: list[ThemeMatchOut]


# -- Outlook --

class OutlookDriverOut(BaseModel):
    title:      str
    commentary: str
    status:     Optional[str]   # Increase / Decrease / Neutral


class ClientOutlookOut(BaseModel):
    headline_outlook: str
    drivers:          list[OutlookDriverOut]
    generated_at:     Optional[datetime]


# -- Fund Recommendations --

class ScoreBreakdownOut(BaseModel):
    theme_alignment: int
    diversification: int
    performance:     int
    cost_efficiency: int
    risk_match:      int


class FundRecommendationOut(BaseModel):
    rank:                     int
    fund_id:                  str
    fund_name:                str
    action:                   str    # BUY / HOLD / SWITCH / SELL
    priority:                 str    # High / Medium / Low
    total_score:              int
    score_breakdown:          ScoreBreakdownOut
    rationale:                str
    suggested_allocation_pct: float


class ClientFundRecommendationOut(BaseModel):
    mifid_suitability:   str                        # "All Pass – Suitability validated against ..."
    portfolio_rationale: str
    recommendations:     list[FundRecommendationOut]
    generated_at:        Optional[datetime]


# -- AI Talking Points --

class AITalkingPointsOut(BaseModel):
    conversation_openers:   Optional[list]
    portfolio_discussion:   Optional[list]
    product_introduction:   Optional[list]
    anticipated_objections: Optional[list]


# ═══════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════

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
            holdings_out = []
            for h in pf.holdings:
                sec = h.security
                pnl = round(((sec.last_price or 0) - (h.avg_cost or 0)) * h.quantity, 2)
                holdings_out.append(HoldingOut(
                    ticker        = sec.ticker,
                    security_name = sec.name,
                    sector        = sec.sector.name if sec.sector else None,
                    security_type = sec.security_type,
                    quantity      = h.quantity,
                    avg_cost      = h.avg_cost,
                    current_price = sec.last_price,
                    current_value = h.current_value,
                    weight_pct    = h.weight_pct,
                    pnl           = pnl,
                ))
            portfolios_out.append(PortfolioOut(
                portfolio_code = pf.portfolio_code,
                name           = pf.name,
                strategy       = pf.strategy,
                total_value    = pf.total_value or 0.0,
                last_valued_at = pf.last_valued_at,
                holdings       = holdings_out,
            ))

    return ClientOut(
        client_id        = client.id,
        client_code      = client.client_code,
        name             = client.name,
        risk_profile     = client.risk_profile,
        age              = client.age,
        profession       = client.profession,
        preference       = client.preference,
        service_model    = client.service_model,
        investment_goals = client.investment_goals,
        portfolios       = portfolios_out,
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
            theme_id        = m.theme_id,
            theme_name      = m.theme.name,
            matched_sectors = json.loads(m.matched_sectors or "[]"),
            exposure_value  = m.exposure_value,
            exposure_pct    = m.exposure_pct,
            sentiment       = m.sentiment.value if m.sentiment else None,
            confidence      = m.confidence,
            matched_at      = m.matched_at,
        )
        for m in matches
    ]


# ═══════════════════════════════════════════════
#  ENDPOINTS
# ═══════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# ── Clients ──────────────────────────────────────

@app.get("/clients", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    """List all clients with portfolios."""
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
    """Client portfolio holdings only."""
    return _build_client_out(_client_or_404(db, client_id))


@app.get("/clients/{client_id}/personal", response_model=PersonalDetailsOut)
def get_client_personal(client_id: int, db: Session = Depends(get_db)):
    """Client personal details and constraints."""
    _client_or_404(db, client_id)
    pd = db.query(ClientPersonalDetails).filter_by(client_id=client_id).first()
    if not pd:
        raise HTTPException(status_code=404, detail="No personal details found")
    return PersonalDetailsOut(
        marital_status     = pd.marital_status,
        kids_details       = pd.kids_details,
        date_of_Birth      = pd.date_of_Birth,
        hobbies            = pd.hobbies,
        other              = pd.other,
        client_constraints = pd.client_constraints,
    )


@app.get("/clients/{client_id}/risk", response_model=RiskOverviewOut)
def get_client_risk(client_id: int, db: Session = Depends(get_db)):
    """Client risk overview."""
    _client_or_404(db, client_id)
    r = db.query(ClientRiskOverview).filter_by(client_id=client_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="No risk overview found")
    return RiskOverviewOut(
        concentration_pct   = r.concentration_pct,
        concentration_asset = r.concentration_asset,
        sharpe_ratio        = r.sharpe_ratio,
        value_at_risk       = r.value_at_risk,
        max_drawdown        = r.max_drawdown,
    )


@app.get("/clients/{client_id}/preferences", response_model=list[PreferenceOut])
def get_client_preferences(client_id: int, db: Session = Depends(get_db)):
    """Client asset class preference bandwidths."""
    _client_or_404(db, client_id)
    prefs = db.query(ClientPreference).filter_by(client_id=client_id).all()
    return [
        PreferenceOut(
            security_type = p.security_type,
            bandwidth_min = p.bandwidth_min,
            bandwidth_max = p.bandwidth_max,
        )
        for p in prefs
    ]


@app.get("/clients/{client_id}/meeting", response_model=MeetingOut)
def get_client_meeting(client_id: int, db: Session = Depends(get_db)):
    """Upcoming meeting details."""
    _client_or_404(db, client_id)
    m = db.query(Meeting).filter_by(client_id=client_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="No meeting found")
    return MeetingOut(title=m.title, date=m.date, location=m.location, platform=m.platform)


@app.get("/clients/{client_id}/meeting-summary", response_model=MeetingSummaryOut)
def get_client_meeting_summary(client_id: int, db: Session = Depends(get_db)):
    """Last meeting discussion points and client questions."""
    _client_or_404(db, client_id)
    s = db.query(ClientMeetingSummary).filter_by(client_id=client_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="No meeting summary found")
    return MeetingSummaryOut(
        main_discussion_points = s.main_discussion_points,
        client_questions       = s.client_questions,
        last_meeting_date      = s.last_meeting_date,
    )


@app.get("/clients/{client_id}/transactions", response_model=list[TransactionOut])
def get_client_transactions(client_id: int, db: Session = Depends(get_db)):
    """Recent transactions for client accounts."""
    client = _client_or_404(db, client_id)
    txns   = []
    for account in client.accounts:
        txns.extend(account.transactions)
    txns.sort(key=lambda t: t.transaction_date, reverse=True)
    return [
        TransactionOut(
            transaction_type = t.transaction_type,
            ticker           = t.ticker,
            product_name     = t.product_name,
            amount           = t.amount,
            currency         = t.currency,
            transaction_date = t.transaction_date,
        )
        for t in txns
    ]


@app.get("/clients/{client_id}/themes", response_model=list[ThemeMatchOut])
def get_client_themes(client_id: int, db: Session = Depends(get_db)):
    """Matched investment themes."""
    _client_or_404(db, client_id)
    return _build_theme_matches(db, client_id)


@app.get("/clients/{client_id}/overview", response_model=ClientOverviewOut)
def get_client_overview(client_id: int, db: Session = Depends(get_db)):
    """Combined portfolio + themes — main mid-tier endpoint."""
    client = _client_or_404(db, client_id)
    return ClientOverviewOut(
        client         = _build_client_out(client),
        matched_themes = _build_theme_matches(db, client_id),
    )


@app.get("/clients/{client_id}/outlook", response_model=ClientOutlookOut)
def get_client_outlook(client_id: int, db: Session = Depends(get_db)):
    """AI-generated market outlook (step 5 output)."""
    _client_or_404(db, client_id)
    outlook = db.query(ClientOutlook).filter_by(client_id=client_id).first()
    if not outlook:
        raise HTTPException(status_code=404, detail="No outlook generated yet — run step 5")
    return ClientOutlookOut(
        headline_outlook = outlook.headline_outlook,
        drivers          = json.loads(outlook.drivers or "[]"),
        generated_at     = outlook.generated_at,
    )


@app.get("/clients/{client_id}/recommendations", response_model=ClientFundRecommendationOut)
def get_client_recommendations(client_id: int, db: Session = Depends(get_db)):
    """AI-scored fund recommendations (step 6 output)."""
    _client_or_404(db, client_id)
    rec = db.query(ClientFundRecommendation).filter_by(client_id=client_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="No recommendations generated yet — run step 8")
    return ClientFundRecommendationOut(
        mifid_suitability   = rec.mifid_suitability or "",
        portfolio_rationale = rec.portfolio_rationale or "",
        recommendations     = json.loads(rec.recommendations or "[]"),
        generated_at        = rec.generated_at,
    )


@app.get("/clients/{client_id}/talking-points", response_model=AITalkingPointsOut)
def get_client_talking_points(client_id: int, db: Session = Depends(get_db)):
    """AI-generated RM talking points for client meeting."""
    _client_or_404(db, client_id)
    tp = db.query(ClientAITalkingPoints).filter_by(client_id=client_id).first()
    if not tp:
        raise HTTPException(status_code=404, detail="No talking points found")
    return AITalkingPointsOut(
        conversation_openers   = tp.conversation_openers,
        portfolio_discussion   = tp.portfolio_discussion,
        product_introduction   = tp.product_introduction,
        anticipated_objections = tp.anticipated_objections,
    )


# ── Securities ────────────────────────────────────

@app.get("/securities/{ticker}/price-history", response_model=list[PriceHistoryOut])
def get_price_history(ticker: str, db: Session = Depends(get_db)):
    """Monthly price history for a security."""
    history = (
        db.query(SecurityPriceHistory)
        .filter_by(ticker=ticker)
        .order_by(SecurityPriceHistory.year, SecurityPriceHistory.month)
        .all()
    )
    if not history:
        raise HTTPException(status_code=404, detail=f"No price history for {ticker}")
    return [
        PriceHistoryOut(ticker=h.ticker, month=h.month, year=h.year, price=h.price)
        for h in history
    ]


# ── News ──────────────────────────────────────────

@app.get("/news/recent")
def get_recent_news(limit: int = 20, db: Session = Depends(get_db)):
    """Recent ingested news articles."""
    articles = (
        db.query(NewsArticle)
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "title":        a.title,
            "url":          a.url,
            "published_at": a.published_at,
            "source_name":  a.source_name,
            "summary":      a.summary,
        }
        for a in articles
    ]