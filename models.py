"""
models.py  –  SQLAlchemy ORM for the Finance Pipeline

Entity hierarchy
────────────────
NewsArticle  →  MarketEvent  →  Trend  →  Theme
                                            └→  SectorTag (sector + sentiment)

Client / Portfolio side
────────────────────────
Client → Account → Portfolio → Holding → Security → SectorMaster
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Float,
    DateTime, Text, ForeignKey, Boolean, Enum, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum

Base = declarative_base()


# ═══════════════════════════════════════════════
#  ENUMERATIONS
# ═══════════════════════════════════════════════

class SentimentEnum(str, enum.Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL  = "Neutral"
    MIXED    = "Mixed"

class TrendDirectionEnum(str, enum.Enum):
    BULLISH  = "Bullish"
    BEARISH  = "Bearish"
    SIDEWAYS = "Sideways"
    UNKNOWN  = "Unknown"

class AccountTypeEnum(str, enum.Enum):
    INDIVIDUAL  = "Individual"
    JOINT       = "Joint"
    RETIREMENT  = "Retirement"
    CORPORATE   = "Corporate"


# ═══════════════════════════════════════════════
#  NEWS / MARKET INTELLIGENCE
# ═══════════════════════════════════════════════

class NewsArticle(Base):
    """Raw ingested article from RSS feed."""
    __tablename__ = "news_articles"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    guid          = Column(String(512), unique=True, nullable=False)   # RSS guid / link hash
    source_name   = Column(String(128))                                # e.g. "Yahoo Finance"
    title         = Column(String(512), nullable=False)
    summary       = Column(Text)
    full_text     = Column(Text)                                       # scraped via newspaper3k
    url           = Column(String(1024))
    published_at  = Column(DateTime)
    ingested_at   = Column(DateTime, default=datetime.utcnow)
    raw_file_path = Column(String(512))                                # path to saved JSON file
    is_processed  = Column(Boolean, default=False)

    # ── relationships ─────────────────────────
    market_events = relationship("MarketEvent", back_populates="article",
                                 cascade="all, delete-orphan")

    def __repr__(self):
        return f"<NewsArticle id={self.id} title='{self.title[:50]}...'>"


class MarketEvent(Base):
    """
    AI-extracted discrete market event from an article.
    One article can yield multiple events.
    e.g. "Fed raises rates by 25bps", "NVDA beats earnings"
    """
    __tablename__ = "market_events"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    article_id     = Column(Integer, ForeignKey("news_articles.id"), nullable=False)
    event_text     = Column(Text, nullable=False)      # short event description
    event_type     = Column(String(64))                # EARNINGS / MACRO / M&A / REGULATORY etc.
    entities       = Column(Text)                      # JSON: companies, tickers mentioned
    extracted_at   = Column(DateTime, default=datetime.utcnow)

    # ── relationships ─────────────────────────
    article        = relationship("NewsArticle", back_populates="market_events")
    trend_links    = relationship("MarketEventTrend", back_populates="market_event",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MarketEvent id={self.id} type={self.event_type}>"


class Trend(Base):
    """
    A named trend that groups related market events.
    e.g. "AI Chip Supply Squeeze", "Rising Interest Rate Environment"
    """
    __tablename__ = "trends"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    name           = Column(String(256), nullable=False)
    description    = Column(Text)
    direction      = Column(Enum(TrendDirectionEnum), default=TrendDirectionEnum.UNKNOWN)
    first_seen_at  = Column(DateTime, default=datetime.utcnow)
    last_updated   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── relationships ─────────────────────────
    event_links    = relationship("MarketEventTrend", back_populates="trend",
                                  cascade="all, delete-orphan")
    theme_links    = relationship("TrendTheme", back_populates="trend",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trend id={self.id} name='{self.name}'>"


class MarketEventTrend(Base):
    """Many-to-many: MarketEvent ↔ Trend."""
    __tablename__ = "market_event_trends"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    market_event_id= Column(Integer, ForeignKey("market_events.id"), nullable=False)
    trend_id       = Column(Integer, ForeignKey("trends.id"), nullable=False)
    relevance_score= Column(Float, default=1.0)       # 0-1 AI confidence

    market_event   = relationship("MarketEvent", back_populates="trend_links")
    trend          = relationship("Trend",        back_populates="event_links")

    __table_args__ = (
        UniqueConstraint("market_event_id", "trend_id", name="uq_event_trend"),
    )


class Theme(Base):
    """
    High-level investment theme grouping multiple trends.
    e.g. "AI Revolution", "Energy Transition", "Deglobalization"
    """
    __tablename__ = "themes"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    name           = Column(String(256), nullable=False, unique=True)
    description    = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)
    last_updated   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── relationships ─────────────────────────
    trend_links    = relationship("TrendTheme", back_populates="theme",
                                  cascade="all, delete-orphan")
    sector_tags    = relationship("SectorTag", back_populates="theme",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Theme id={self.id} name='{self.name}'>"


class TrendTheme(Base):
    """Many-to-many: Trend ↔ Theme."""
    __tablename__ = "trend_themes"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    trend_id       = Column(Integer, ForeignKey("trends.id"), nullable=False)
    theme_id       = Column(Integer, ForeignKey("themes.id"), nullable=False)
    weight         = Column(Float, default=1.0)

    trend          = relationship("Trend", back_populates="theme_links")
    theme          = relationship("Theme", back_populates="trend_links")

    __table_args__ = (
        UniqueConstraint("trend_id", "theme_id", name="uq_trend_theme"),
    )


class SectorTag(Base):
    """
    Sector + sentiment tagged to a Theme.
    e.g.  Theme: 'AI Revolution' → sector: 'Semiconductors', sentiment: Positive
    """
    __tablename__ = "sector_tags"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    theme_id       = Column(Integer, ForeignKey("themes.id"), nullable=False)
    sector_name    = Column(String(128), nullable=False)   # maps to SectorMaster
    sentiment      = Column(Enum(SentimentEnum), nullable=False)
    confidence     = Column(Float, default=1.0)            # AI confidence 0-1
    rationale      = Column(Text)                          # AI explanation
    tagged_at      = Column(DateTime, default=datetime.utcnow)

    theme          = relationship("Theme", back_populates="sector_tags")

    def __repr__(self):
        return (f"<SectorTag theme_id={self.theme_id} "
                f"sector='{self.sector_name}' sentiment={self.sentiment}>")


# ═══════════════════════════════════════════════
#  CLIENT / PORTFOLIO DOMAIN
# ═══════════════════════════════════════════════

class SectorMaster(Base):
    """Reference table for all known sectors / industries."""
    __tablename__ = "sector_master"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    name           = Column(String(128), unique=True, nullable=False)
    gics_code      = Column(String(16))    # GICS sector code (optional)
    description    = Column(Text)

    securities     = relationship("Security", back_populates="sector")

    def __repr__(self):
        return f"<SectorMaster name='{self.name}'>"


class Client(Base):
    __tablename__ = "clients"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    client_code    = Column(String(32), unique=True, nullable=False)
    name           = Column(String(256), nullable=False)
    email          = Column(String(256))
    phone          = Column(String(32))
    risk_profile   = Column(String(32))   # Conservative / Moderate / Aggressive
    created_at     = Column(DateTime, default=datetime.utcnow)

    accounts       = relationship("Account", back_populates="client",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client code={self.client_code} name='{self.name}'>"


class Account(Base):
    __tablename__ = "accounts"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    account_number = Column(String(64), unique=True, nullable=False)
    client_id      = Column(Integer, ForeignKey("clients.id"), nullable=False)
    account_type   = Column(Enum(AccountTypeEnum), default=AccountTypeEnum.INDIVIDUAL)
    currency       = Column(String(8), default="USD")
    is_active      = Column(Boolean, default=True)
    opened_at      = Column(DateTime, default=datetime.utcnow)

    client         = relationship("Client",    back_populates="accounts")
    portfolios     = relationship("Portfolio", back_populates="account",
                                  cascade="all, delete-orphan")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_code = Column(String(64), unique=True, nullable=False)
    account_id     = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    name           = Column(String(256))
    strategy       = Column(String(128))     # Growth / Income / Balanced etc.
    inception_date = Column(DateTime)
    total_value    = Column(Float, default=0.0)
    last_valued_at = Column(DateTime)

    account        = relationship("Account",  back_populates="portfolios")
    holdings       = relationship("Holding",  back_populates="portfolio",
                                  cascade="all, delete-orphan")


class Security(Base):
    __tablename__ = "securities"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    ticker         = Column(String(16), unique=True, nullable=False)
    name           = Column(String(256))
    isin           = Column(String(12))
    security_type  = Column(String(32))   # EQUITY / ETF / BOND / CRYPTO
    exchange       = Column(String(32))   # NYSE / NASDAQ / LSE
    sector_id      = Column(Integer, ForeignKey("sector_master.id"))
    currency       = Column(String(8), default="USD")
    last_price     = Column(Float)
    last_price_at  = Column(DateTime)

    sector         = relationship("SectorMaster", back_populates="securities")
    holdings       = relationship("Holding",      back_populates="security")


class Holding(Base):
    __tablename__ = "holdings"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id   = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    security_id    = Column(Integer, ForeignKey("securities.id"), nullable=False)
    quantity       = Column(Float, nullable=False)
    avg_cost       = Column(Float)
    current_value  = Column(Float)
    weight_pct     = Column(Float)             # % of portfolio
    as_of_date     = Column(DateTime, default=datetime.utcnow)

    portfolio      = relationship("Portfolio", back_populates="holdings")
    security       = relationship("Security",  back_populates="holdings")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "security_id", name="uq_portfolio_security"),
    )

class ClientThemeMatch(Base):
    """
    Step 3 output: which themes are relevant to which client's holdings,
    and how much portfolio exposure backs that relevance.
    """
    __tablename__ = "client_theme_matches"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    client_id     = Column(Integer, ForeignKey("clients.id"), nullable=False)
    theme_id      = Column(Integer, ForeignKey("themes.id"), nullable=False)
    matched_at    = Column(DateTime, default=datetime.utcnow)

    # Which sectors in the portfolio triggered this match
    matched_sectors = Column(Text)          # JSON list e.g. ["Semiconductors","Technology"]
    # Total portfolio value exposed to this theme
    exposure_value  = Column(Float, default=0.0)
    # % of portfolio exposed
    exposure_pct    = Column(Float, default=0.0)
    # Highest sentiment from SectorTags for this theme
    sentiment       = Column(Enum(SentimentEnum))
    # Highest confidence score across matched tags
    confidence      = Column(Float, default=0.0)

    client = relationship("Client")
    theme  = relationship("Theme")

    __table_args__ = (
        UniqueConstraint("client_id", "theme_id", name="uq_client_theme"),
    )

# ═══════════════════════════════════════════════
#  DB FACTORY
# ═══════════════════════════════════════════════

def get_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, echo=False)

def get_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db(database_url: str):
    """Create all tables if they don't exist."""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return engine
