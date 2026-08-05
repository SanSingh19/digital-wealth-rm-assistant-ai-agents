"""
step8_recommend.py – Step 8: Sector-Level AI Recommendations

Goal: For each sector a client holds, produce a BUY / HOLD / SELL action
      with a 1-line description, driven entirely by existing pipeline data.

Architecture
────────────
  INPUTS (all from existing DB — no new data fetched)
    1. Client holdings       → which sectors the client is exposed to
    2. ClientOutlook.drivers → [{title, commentary, status: Increase/Decrease/Neutral}]
    3. ClientThemeMatch      → themes matched to client + sentiment per theme
    4. SectorTag             → sector-level sentiment from step 2 AI processing
    5. ClientPersonalDetails → client_constraints (hard rules)

  SIGNAL SCORING (pure Python — deterministic, no LLM)
    For each sector the client holds:

      Signal 1 — Outlook driver status (weight 50%)
        Scan all drivers for keywords matching this sector
        Increase → +1,  Neutral → 0,  Decrease → -1

      Signal 2 — Theme sentiment (weight 30%)
        Scan themes matched to this client that cover this sector
        Positive → +1,  Mixed/Neutral → 0,  Negative → -1

      Signal 3 — SectorTag sentiment from processed news (weight 20%)
        Scan SectorTag rows for this sector name
        Positive → +1,  Mixed/Neutral → 0,  Negative → -1

      Weighted score = (s1 * 0.5) + (s2 * 0.3) + (s3 * 0.2)

      score >  0.3  → BUY
      score < -0.3  → SELL
      otherwise     → HOLD

  DESCRIPTION GENERATION (1 LLM call per client — not per sector)
    Pass all sector signals + client context to GPT-4o
    LLM writes one punchy sentence per sector referencing actual drivers/themes

  OUTPUT → client_sector_recommendations table (upserted each run)
    sector_name, action, signal_score, description

Flow: Step 3 → Step 5 → Step 8
"""

import json
import logging
import ssl
import sys
from datetime import datetime
from pathlib import Path

# -- SSL fix ------------------------------------
ssl._create_default_https_context = ssl._create_unverified_context
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import httpx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from sqlalchemy.orm import joinedload, Session

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.settings import DATABASE_URL, OPENAI_API_KEY
from models import (
    init_db, get_session_factory,
    Client, Account, Portfolio, Holding, Security,
    ClientThemeMatch, ClientOutlook, ClientPersonalDetails,
    SectorTag, Theme,
    SectorMaster,
    ClientSectorRecommendation,
    ClientFundRecommendation
)

log = logging.getLogger("step8_recommend")


# ==============================================
#  SECTOR KEYWORD MAP
#  Maps sector names → keywords to scan in
#  driver titles and theme names
# ==============================================

SECTOR_KEYWORDS: dict[str, list[str]] = {
    "Technology":           ["tech", "technology", "software", "cloud", "ai", "microsoft", "apple", "msft", "aapl"],
    "Semiconductors":       ["semiconductor", "chip", "nvidia", "asml", "amd", "nvda"],
    "Financials":           ["bank", "financ", "rate", "bond", "ecb", "fed", "interest", "credit"],
    "Energy":               ["energy", "oil", "gas", "opec", "crude"],
    "Renewable Energy":     ["renewable", "solar", "wind", "green", "esg", "climate", "nordea", "alt"],
    "Real Estate":          ["real estate", "reit", "property", "housing", "flats", "house"],
    "Consumer Discretionary": ["consumer", "retail", "tesla", "amazon", "flipkart"],
    "Healthcare":           ["health", "pharma", "biotech", "drug", "medical"],
    "Utilities":            ["utility", "utilities", "power", "electric"],
    "Industrials":          ["industrial", "manufacturing", "factory", "automation", "robotics", "infrastructure", "construction", "engineering", "machinery", "capital goods", "caterpillar", "siemens"],
    "Communication Services": ["communication","AI","Interest Rates","Fed","NVIDIA","Semiconductor", "telecom", "media","communication", "streaming", "advertising", "social media", "internet", "digital platform", "meta", "facebook", "google", "alphabet", "youtube"],
    "Materials":             ["materials", "mining", "metals", "steel", "aluminium", "aluminum", "copper", "commodity", "commodities", "gold", "silver", "lithium", "iron ore", "rio tinto", "bhp"],
    "Utilities":             ["utilities","electric", "utility", "electricity", "power", "power grid", "grid", "renewable grid", "water", "gas distribution", "electric utility", "energy distribution", "next era", "nextera", "enel"],
    "E-Commerce":            ["e-commerce", "ecommerce", "online retail", "digital commerce", "online shopping", "marketplace", "consumer internet", "retail", "amazon", "shopify", "flipkart", "ebay", "etsy"],
    "Cryptocurrency":        ["bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", "blockchain", "digital asset", "digital assets", "stablecoin", "web3", "defi", "token", "coinbase", "binance"],
    "Small Cap": ["small cap", "small-cap", "mid cap", "mid-cap", "growth companies", "emerging companies", "high growth", "small capitalization", "small business"],
    "Artificial Intelligence": ["ai", "artificial intelligence", "machine learning", "deep learning", "generative ai", "chatgpt", "llm", "openai", "copilot", "automation", "ai infrastructure"],
    "Cloud Computing": ["cloud", "cloud computing", "azure", "aws", "amazon web services", "google cloud", "gcp", "saas", "software as a service", "cloud infrastructure"],
    "Digital Infrastructure": ["digital infrastructure", "data center", "datacenter", "server", "compute", "gpu", "network", "fiber", "5g", "hyperscaler", "digital backbone"],
    "Cybersecurity": ["cybersecurity", "cyber", "security", "ransomware", "endpoint", "firewall", "identity security", "crowdstrike", "palo alto", "zero trust"],
    "Blockchain": ["blockchain", "distributed ledger", "smart contract", "web3", "ethereum", "bitcoin", "tokenization", "crypto infrastructure"]

}

# Sentiment → numeric score
SENTIMENT_SCORE = {
    "Positive":  1.0,
    "Increase":  1.0,
    "Neutral":   0.0,
    "Mixed":     0.0,
    "Sideways":  0.0,
    "Negative": -1.0,
    "Decrease": -1.0,
}

# Score thresholds
BUY_THRESHOLD  =  0.3
SELL_THRESHOLD = -0.3


# ==============================================
#  PYDANTIC OUTPUT SCHEMA
# ==============================================

class SectorDescription(BaseModel):
    sector_name: str  = Field(description="Exact sector name as provided")
    description: str  = Field(
        description=(
            "One punchy sentence explaining WHY this action makes sense. "
            "Reference the actual market driver, theme, or news event. "
            "E.g. 'AI chip demand surge and ASML's strong order book support accumulation.' "
            "or 'ECB rate hold at 2.75% pressures bond valuations — consider reducing duration.' "
            "Never generic — always tied to real data."
        )
    )


class SectorRecommendationsResult(BaseModel):
    sector_descriptions: list[SectorDescription] = Field(
        description="One description per sector, matching the sector names provided."
    )

class InvestmentRecommendation(BaseModel):

    rank: int = Field( description="Recommendation ranking")
    recommendation_type: str = Field(description="SECURITY or FUND")
    investment_id: str = Field(description="Ticker or Fund ID")
    investment_name: str = Field( description="Security name or Fund name")
    sector: str = Field( description="Sector")
    action: str = Field(description="Always BUY")
    priority: str = Field(description="High / Medium / Low")
    rationale: str = Field(
        description="One concise sentence explaining why this investment is recommended."
    )


class InvestmentRecommendationResult(BaseModel):

    mifid_suitability: str = Field(
        description="One concise MiFID suitability statement (maximum 15 words)."
    )

    portfolio_rationale: str = Field(
        description="Overall summary of why these recommendations fit the client."
    )


    recommendations: list[InvestmentRecommendation]


PARSER = PydanticOutputParser(pydantic_object=SectorRecommendationsResult)
FUND_RECOMMENDATION_PARSER = PydanticOutputParser(pydantic_object=InvestmentRecommendationResult)

PROMPT = ChatPromptTemplate.from_template(
    """You are a wealth management advisor. Write one-sentence descriptions for each
sector recommendation below. Each sentence must reference a specific market event,
driver, or theme — never generic statements.

CLIENT
───────
Name:         {client_name}
Risk Profile: {risk_profile}
Constraints:  {constraints}

SECTOR RECOMMENDATIONS TO DESCRIBE
─────────────────────────────────────
{sector_signals_text}

MARKET CONTEXT (use this to write descriptions)
─────────────────────────────────────────────────
Outlook Drivers:
{drivers_text}

Matched Themes:
{themes_text}

INSTRUCTIONS
─────────────
- Write exactly one description per sector listed above.
- Each description must be one sentence, max 20 words.
- Reference what is actually happening (driver title, theme name, specific event).
- Match the tone to the action: BUY → positive/opportunistic, SELL → cautionary, HOLD → balanced.
- Never say "based on analysis" or "considering the market" — be direct.

{format_instructions}
"""
)

# ==============================================
# FUND UNIVERSE
# ==============================================

FUND_UNIVERSE = {

    "Technology": [

        {
            "fund_id": "F001",
            "fund_name": "Global Technology Leaders Fund",
            "risk": "Moderate",
            "sector": "Technology",
            "investment_style": "Growth"
        },

        {
            "fund_id": "F002",
            "fund_name": "Digital Innovation Fund",
            "risk": "Aggressive",
            "sector": "Technology",
            "investment_style": "Growth"
        }

    ],

    "Semiconductors": [

        {
            "fund_id": "F003",
            "fund_name": "Global Semiconductor Growth Fund",
            "risk": "Aggressive",
            "sector": "Semiconductors",
            "investment_style": "Growth"
        },

        {
            "fund_id": "F004",
            "fund_name": "AI Infrastructure Leaders Fund",
            "risk": "Moderate",
            "sector": "Semiconductors",
            "investment_style": "Growth"
        }

    ],

    "Financials": [

        {
            "fund_id": "F005",
            "fund_name": "European Financial Opportunities Fund",
            "risk": "Moderate",
            "sector": "Financials",
            "investment_style": "Balanced"
        },

        {
            "fund_id": "F006",
            "fund_name": "Dividend Income Fund",
            "risk": "Conservative",
            "sector": "Financials",
            "investment_style": "Income"
        }

    ],

    "Healthcare": [

        {
            "fund_id": "F007",
            "fund_name": "Global Healthcare Leaders Fund",
            "risk": "Moderate",
            "sector": "Healthcare",
            "investment_style": "Growth"
        },

        {
            "fund_id": "F0202",
            "fund_name": "Healthcare Opportunities ESG Fund",
            "risk": "Moderate",
            "sector": "Healthcare",
            "investment_style": "Balanced"
        },

        {
            "fund_id": "F0230",
            "fund_name": "Global Life Sciences Growth Fund",
            "risk": "Aggressive",
            "sector": "Healthcare",
            "investment_style": "Growth"
        }

    ],

    "Renewable Energy": [

        {
            "fund_id": "F008",
            "fund_name": "Clean Energy Growth Fund",
            "risk": "Aggressive",
            "sector": "Renewable Energy",
            "investment_style": "Growth"
        }

    ],

    "Consumer Discretionary": [

        {
            "fund_id": "F013",
            "fund_name": "Global Consumer Growth Fund",
            "risk": "Moderate",
            "sector": "Consumer Discretionary",
            "investment_style": "Growth"
        },

        {
            "fund_id": "F014",
            "fund_name": "Consumer Lifestyle Opportunities Fund",
            "risk": "Aggressive",
            "sector": "Consumer Discretionary",
            "investment_style": "Growth"
        }

    ],

    "Energy": [

        {
            "fund_id": "F009",
            "fund_name": "Global Energy Opportunities Fund",
            "risk": "Moderate",
            "sector": "Energy",
            "investment_style": "Balanced"
        }

    ],

    "Real Estate": [

        {
            "fund_id": "F010",
            "fund_name": "European Real Estate Income Fund",
            "risk": "Conservative",
            "sector": "Real Estate",
            "investment_style": "Income"
        }

    ],

    "Industrials": [
        {
            "fund_id": "F015",
            "fund_name": "Global Industrials Leaders Fund",
            "risk": "Moderate",
            "sector": "Industrials",
            "investment_style": "Growth"
        },
        {
            "fund_id": "F016",
            "fund_name": "Infrastructure Opportunities Fund",
            "risk": "Moderate",
            "sector": "Industrials",
            "investment_style": "Balanced"
        },
        {
            "fund_id": "F017",
            "fund_name": "Smart Manufacturing Growth Fund",
            "risk": "Aggressive",
            "sector": "Industrials",
            "investment_style": "Growth"
        }
    ],

    "Communication Services": [
        {
            "fund_id": "F018",
            "fund_name": "Global Communication Leaders Fund",
            "risk": "Moderate",
            "sector": "Communication Services",
            "investment_style": "Growth"
        },
        {
            "fund_id": "F019",
            "fund_name": "Digital Media Opportunities Fund",
            "risk": "Aggressive",
            "sector": "Communication Services",
            "investment_style": "Growth"
        }
    ],

    "Materials": [
        {
            "fund_id": "F020",
            "fund_name": "Global Materials Leaders Fund",
            "risk": "Moderate",
            "sector": "Materials",
            "investment_style": "Balanced"
        },
        {
            "fund_id": "F021",
            "fund_name": "Commodity Growth Fund",
            "risk": "Aggressive",
            "sector": "Materials",
            "investment_style": "Growth"
        }
    ],

    "Utilities": [
        {
            "fund_id": "F022",
            "fund_name": "Global Utilities Income Fund",
            "risk": "Conservative",
            "sector": "Utilities",
            "investment_style": "Income"
        },
        {
            "fund_id": "F023",
            "fund_name": "Essential Infrastructure Fund",
            "risk": "Moderate",
            "sector": "Utilities",
            "investment_style": "Balanced"
        }
    ],

    "E-Commerce": [
        {
            "fund_id": "F024",
            "fund_name": "Global E-Commerce Growth Fund",
            "risk": "Moderate",
            "sector": "E-Commerce",
            "investment_style": "Growth"
        },
        {
            "fund_id": "F025",
            "fund_name": "Digital Commerce Innovation Fund",
            "risk": "Aggressive",
            "sector": "E-Commerce",
            "investment_style": "Growth"
        }
    ],

    "Small Cap": [
        {
            "fund_id": "F028",
            "fund_name": "Global Small Cap Growth Fund",
            "risk": "Aggressive",
            "sector": "Small Cap",
            "investment_style": "Growth"
        },
        {
            "fund_id": "F029",
            "fund_name": "Emerging Companies Fund",
            "risk": "Moderate",
            "sector": "Small Cap",
            "investment_style": "Growth"
        }
    ],

    "Artificial Intelligence": [
        {
            "fund_id": "F030",
            "fund_name": "AI Innovation Fund",
            "risk": "Aggressive",
            "sector": "Artificial Intelligence",
            "investment_style": "Growth"
        },
        {
            "fund_id": "F031",
            "fund_name": "Global AI Leaders Fund",
            "risk": "Moderate",
            "sector": "Artificial Intelligence",
            "investment_style": "Growth"
        }
    ],

    "Cloud Computing": [
        {
            "fund_id": "F032",
            "fund_name": "Cloud Infrastructure Fund",
            "risk": "Moderate",
            "sector": "Cloud Computing",
            "investment_style": "Growth"
        },
        {
            "fund_id": "F033",
            "fund_name": "Global Cloud Leaders Fund",
            "risk": "Aggressive",
            "sector": "Cloud Computing",
            "investment_style": "Growth"
        }
    ],

    "Cloud Computing": [
        {
            "fund_id": "F032",
            "fund_name": "Cloud Infrastructure Fund",
            "risk": "Moderate",
            "sector": "Cloud Computing",
            "investment_style": "Growth"
        },
        {
            "fund_id": "F033",
            "fund_name": "Global Cloud Leaders Fund",
            "risk": "Aggressive",
            "sector": "Cloud Computing",
            "investment_style": "Growth"
        }
    ],

    "Cryptocurrency": [
        {
            "fund_id": "F026",
            "fund_name": "Digital Assets Strategy Fund",
            "risk": "Aggressive",
            "sector": "Cryptocurrency",
            "investment_style": "Growth"
        },
        {
            "fund_id": "F027",
            "fund_name": "Blockchain Innovation Fund",
            "risk": "Aggressive",
            "sector": "Cryptocurrency",
            "investment_style": "Growth"
        }
    ]

}

FUND_RECOMMENDATION_PROMPT = ChatPromptTemplate.from_template("""
You are a Senior Wealth Relationship Manager at a leading global private bank.
Recommend investments that maximize client suitability while leveraging current market opportunities.
Client suitability always takes priority over expected return.

========================
CLIENT PROFILE
========================
Client Name          : {client_name}
Risk Profile         : {risk_profile}
Investment Goals     : {investment_goals}
Profession           : {profession}
Service Model        : {service_model}
Investment Preference: {preference}
Client Constraints   : {constraints}

========================
MARKET CONTEXT
========================

Market Drivers
{drivers_text}

Matched Investment Themes
{themes_text}

========================
SHORTLISTED CANDIDATES
========================

Security Candidates
{candidate_securities}

Fund Candidates
{candidate_funds}

========================
POSITIVE DIVERSIFICATION OPPORTUNITIES
========================

These sectors are NOT currently owned by the client.
Recommend investments ONLY from these sectors.
{positive_opportunity_sectors}

========================
DECISION PROCESS
========================

Step 1 — Suitability
Every recommendation must satisfy:
• Risk Profile
• Investment Goals
• Investment Preference
• Client Constraints
• Existing Portfolio
• Service Model
Reject any investment that violates any requirement.

Step 2 — Market Opportunity
Evaluate remaining investments using:
• Market Drivers
• Investment Themes
• Sector Momentum
• News Sentiment

Step 3 — Portfolio Enhancement
Improve the portfolio by introducing attractive new sector exposure.
Every recommendation must come from the Positive Diversification Opportunities listed above.
Maintain diversification.
Avoid unnecessary concentration.
Recommend multiple investments from one sector only when strongly justified.

Step 4 — Final Ranking

Rank recommendations using the following priority:
1. Client Suitability
2. Portfolio Improvement
3. Market Opportunity
4. Long-term Value Creation

Suitability ALWAYS has higher priority than market momentum.

========================
MANDATORY RULES
========================

You MUST strictly follow every rule below.
MANDATORY RULES:
• Recommend EXACTLY THREE BUY investments.
• Use ONLY investments from the supplied candidate lists.
• Recommend investments ONLY from the Positive Diversification Opportunities.
• Never recommend investments from sectors already owned by the client.
• Never invent, rename, abbreviate, or modify Investment IDs, Names, or Sectors.
• Copy Investment ID, Name, and Sector exactly as provided.
• Do not recommend duplicate investments.
• Every recommendation must satisfy the client's Risk Profile, Goals, Preference, Constraints, and Service Model.
• Prefer different sectors whenever suitable.
• Recommend multiple investments from one sector only when justified.
• Every rationale must explain:
   - why it suits THIS client
   - which market driver, theme, or opportunity supports it.

========================
OUTPUT
========================

Return EXACTLY THREE BUY recommendations.
Each recommendation MUST include:

• Rank
• Recommendation Type (SECURITY or FUND)
• Investment ID
• Investment Name
• Sector
• Action = BUY
• Priority (High / Medium / Low)
• One rationale (maximum 30 words)

Every rationale MUST explain:
1. Why the investment suits THIS client.
2. Which market driver, investment theme, or sector opportunity supports the recommendation.
• Do not describe a Healthcare fund as ESG unless its name or supplied attributes explicitly indicate ESG.
• If the investment is not an ESG fund, explain it using its sector opportunity, diversification benefit and market outlook.
Good examples:
   ✓ Monetary policy easing strengthens financial sector prospects while complementing the client's long-term growth objectives.
   ✓ Positive pharmaceutical innovation supports long-term healthcare growth while improving sector diversification.
   ✓ Communication Services benefits from digital media and technology momentum, complementing the client's aggressive growth strategy.
Bad examples:
   ✗ Supports ESG preference...
   ✗ Aligns with sustainability goals...
   ✗ Green investing opportunity...
   (Only valid if the selected fund is explicitly an ESG fund.)

Avoid generic market commentary.
Write naturally as a Senior Wealth Relationship Manager preparing recommendations for another experienced RM.

========================
MiFID SUITABILITY
========================

Provide ONE concise suitability statement(maximum 15 words).

The statement must explain why the final recommendations are suitable for this client's:

• Risk Profile
• Investment Goals
• Investment Preference
• Client Constraints

Do NOT mention individual investments.
Examples:
• Suitability validated for a Moderate Growth investor with long-term capital appreciation objectives.
• Suitable for a Balanced investor seeking diversified long-term growth within stated constraints.
• Recommendations align with the client's Moderate Offensive profile and long-term investment objectives.

========================
PORTFOLIO RATIONALE
========================

Finally provide one concise portfolio rationale (maximum 60 words) explaining:
• Why these three recommendations were selected
• How they improve diversification
• How they align with the client's goals
• How they respect the client's risk profile
• How they strengthen the long-term portfolio

{format_instructions}
""")

# ==============================================
#  SIGNAL ENGINE (pure Python)
# ==============================================

def _sector_keywords(sector_name: str) -> list[str]:
    """Get keywords for a sector, fallback to lowercase sector name."""
    return SECTOR_KEYWORDS.get(sector_name, [sector_name.lower()])


def _score_from_drivers(sector_name: str, drivers: list[dict]) -> float:
    """
    Signal 1 (weight 50%): scan outlook drivers for sector keywords.
    Returns average status score across matching drivers.
    """
    keywords = _sector_keywords(sector_name)
    scores   = []

    for d in drivers:
        text   = (d.get("title", "") + " " + d.get("commentary", "")).lower()
        status = d.get("status", "Neutral")
        if any(kw in text for kw in keywords):
            scores.append(SENTIMENT_SCORE.get(status, 0.0))

    return sum(scores) / len(scores) if scores else 0.0


def _score_from_themes(sector_name: str, matches: list, session: Session) -> float:
    """
    Signal 2 (weight 30%): scan client theme matches for themes that
    have SectorTag entries matching this sector.
    Returns average sentiment score across matching theme-sector pairs.
    """
    keywords = _sector_keywords(sector_name)
    scores   = []

    for match in matches:
        # Check matched_sectors JSON for this sector
        matched_sectors = json.loads(match.matched_sectors or "[]")
        sector_hit = any(
            any(kw in s.lower() for kw in keywords)
            for s in matched_sectors
        )
        if sector_hit and match.sentiment:
            scores.append(SENTIMENT_SCORE.get(match.sentiment.value, 0.0))

    return sum(scores) / len(scores) if scores else 0.0


def _score_from_sector_tags(sector_name: str, session: Session) -> float:
    """
    Signal 3 (weight 20%): scan SectorTag table for this sector name.
    Returns confidence-weighted average sentiment.
    """
    keywords = _sector_keywords(sector_name)

    tags = session.query(SectorTag).all()
    weighted_scores = []
    total_weight    = 0.0

    for tag in tags:
        tag_lower = tag.sector_name.lower()
        if any(kw in tag_lower for kw in keywords):
            score  = SENTIMENT_SCORE.get(tag.sentiment.value, 0.0)
            weight = tag.confidence
            weighted_scores.append(score * weight)
            total_weight += weight

    return sum(weighted_scores) / total_weight if total_weight > 0 else 0.0


def compute_signal(
    sector_name: str,
    drivers: list[dict],
    matches: list,
    session: Session,
) -> dict:
    """
    Compute weighted signal score for a sector.
    Returns {sector_name, signal_score, action, signals_detail}
    """
    s1 = _score_from_drivers(sector_name, drivers)
    s2 = _score_from_themes(sector_name, matches, session)
    s3 = _score_from_sector_tags(sector_name, session)

    weighted = (s1 * 0.20) + (s2 * 0.30) + (s3 * 0.50)

    if weighted > BUY_THRESHOLD:
        action = "BUY"
    elif weighted < SELL_THRESHOLD:
        action = "SELL"
    else:
        action = "HOLD"

    return {
        "sector_name":   sector_name,
        "signal_score":  round(weighted, 3),
        "action":        action,
        "signals_detail": {
            "driver_signal":     round(s1, 3),
            "theme_signal":      round(s2, 3),
            "sector_tag_signal": round(s3, 3),
        },
    }

def _compute_unowned_sector_signals(
    session,
    drivers,
    matches,
    owned_sector_names,
):
    """
    Compute signals ONLY for sectors the client does NOT own.
    """

    signals = []

    log.info("========== PART 2 ==========")

    sectors = (
        session.query(SectorMaster)
        .order_by(SectorMaster.name)
        .all()
    )

    log.info(
        "SectorMaster contains %d sectors",
        len(sectors),
    )

    for sector in sectors:

        if sector.name in owned_sector_names:
            continue

        sig = compute_signal(
            sector.name,
            drivers,
            matches,
            session,
        )

        signals.append(sig)

        log.info(
            "[PART 2] %-22s -> %-4s (%.2f)",
            sig["sector_name"],
            sig["action"],
            sig["signal_score"],
        )

    return signals

# ==============================================
#  PROMPT BUILDERS
# ==============================================

def _build_sector_signals_text(signals: list[dict]) -> str:
    lines = []
    for s in signals:
        d = s["signals_detail"]
        lines.append(
            f"- {s['sector_name']:<25} -> {s['action']:<4}  "
            f"(score={s['signal_score']:+.2f} | "
            f"driver={d['driver_signal']:+.2f}, "
            f"theme={d['theme_signal']:+.2f}, "
            f"tag={d['sector_tag_signal']:+.2f})"
        )
    return "\n".join(lines)


def _build_drivers_text(drivers: list[dict]) -> str:
    return "\n".join(
        f"- [{d.get('status','Neutral')}] {d.get('title','')}: {d.get('commentary','')}"
        for d in drivers
    ) or "No drivers available."


def _build_themes_text(matches: list) -> str:
    return "\n".join(
        f"- {m.theme.name}: sentiment={m.sentiment.value if m.sentiment else 'N/A'}, "
        f"sectors={m.matched_sectors}"
        for m in matches
    ) or "No themes matched."


# ==============================================
#  DB SAVE
# ==============================================

def _save_sector_recommendations(
    session: Session,
    client_id: int,
    signals: list[dict],
    descriptions: dict[str, str],
):
    """Upsert one row per sector for this client."""
    for sig in signals:
        sector  = sig["sector_name"]
        desc    = descriptions.get(sector, "")
        existing = (
            session.query(ClientSectorRecommendation)
            .filter_by(client_id=client_id, sector_name=sector)
            .first()
        )
        if existing:
            existing.action       = sig["action"]
            existing.signal_score = sig["signal_score"]
            existing.description  = desc
            existing.generated_at = datetime.utcnow()
        else:
            session.add(ClientSectorRecommendation(
                client_id    = client_id,
                sector_name  = sector,
                action       = sig["action"],
                signal_score = sig["signal_score"],
                description  = desc,
            ))
    session.commit()

def _save_fund_recommendations(
    session: Session,
    client_id: int,
    recommendation_result: InvestmentRecommendationResult,
):
    """
    Save AI generated fund recommendations.
    """

    existing = (
        session.query(ClientFundRecommendation)
        .filter_by(client_id=client_id)
        .first()
    )

    recommendation_json = []

    for rec in recommendation_result.recommendations:

        recommendation_json.append(
            {
                "rank": rec.rank,
                "recommendation_type": rec.recommendation_type,
                "investment_id": rec.investment_id,
                "investment_name": rec.investment_name,
                "sector": rec.sector,
                "action": rec.action,
                "priority": rec.priority,
                "rationale": rec.rationale
            }
        )

    if existing:

        existing.generated_at = datetime.utcnow()
        existing.mifid_suitability = (recommendation_result.mifid_suitability )
        existing.portfolio_rationale = (recommendation_result.portfolio_rationale)
        existing.recommendations = json.dumps(
            recommendation_json,
            indent=2
        )

    else:

        session.add(
            ClientFundRecommendation(
                client_id=client_id,
                generated_at=datetime.utcnow(),
                mifid_suitability=recommendation_result.mifid_suitability,
                portfolio_rationale= recommendation_result.portfolio_rationale,
                recommendations=json.dumps(
                    recommendation_json,
                    indent=2
                )
            )
        )

    session.commit()

def _get_candidate_securities(
    session,
    signals,
):

    candidates = []

    for signal in signals:

        securities = (
            session.query(Security)
            .join(SectorMaster)
            .filter( SectorMaster.name == signal["sector_name"])
            .all()
        )

        candidates.extend(securities)

    return candidates

def _build_candidate_text(candidates):
    """
    Converts candidate securities into prompt text.
    """

    if not candidates:
        return "No candidate securities found."

    lines = []

    for security in candidates:

        lines.append(
            f"""
            Ticker : {security.ticker}
            Name : {security.name}
            Sector : {security.sector.name if security.sector else "Unknown"}
            Security Type : {security.security_type}
            """.strip()
        )

    return "\n\n".join(lines)

def _get_candidate_funds(signals):
    """
    Returns all candidate funds belonging to BUY sectors.
    """

    candidate_funds = []

    for signal in signals:
        funds = FUND_UNIVERSE.get(
            signal["sector_name"],
            []
        )
        candidate_funds.extend(funds)

    return candidate_funds

def _build_fund_text(candidate_funds):
    """
    Converts candidate funds into prompt text.
    """

    if not candidate_funds:
        return "No candidate funds found."

    lines = []

    for fund in candidate_funds:

        lines.append(
            f"""
            Fund ID : {fund['fund_id']}
            Fund Name : {fund['fund_name']}
            Sector : {fund['sector']}
            Risk : {fund['risk']}
            Investment Style : {fund['investment_style']}
            """.strip()
        )
    return "\n\n".join(lines)


def _generate_fund_recommendations(
    llm,
    client,
    candidate_securities,
    candidate_funds,
    positive_opportunity_signals,
    drivers_text,
    themes_text,
    constraints
):
    """
    Generates AI-based investment recommendations.
    """

    chain = (
        FUND_RECOMMENDATION_PROMPT
        | llm
        | FUND_RECOMMENDATION_PARSER
    )

    candidate_security_text = _build_candidate_text(
        candidate_securities
    )

    candidate_fund_text = _build_fund_text(
        candidate_funds
    )

    positive_sector_text = "\n".join(
        f"- {s['sector_name']}"
        for s in positive_opportunity_signals
    ) or "None"

    log.info(
        "[PART 2] Candidate Securities=%d | Candidate Funds=%d",
        len(candidate_securities),
        len(candidate_funds),
    )

    result = chain.invoke(
        {
            "client_name": client.name,
            "risk_profile": client.risk_profile or "N/A",
            "investment_goals": client.investment_goals or "N/A",
            "profession": client.profession or "N/A",
            "service_model": client.service_model or "N/A",
            "preference": client.preference or "N/A",
            "constraints": constraints,
            "drivers_text": drivers_text,
            "themes_text": themes_text,
            "candidate_securities": candidate_security_text,
            "candidate_funds": candidate_fund_text,
            "positive_opportunity_sectors": positive_sector_text,
            "format_instructions":
                FUND_RECOMMENDATION_PARSER.get_format_instructions()
        }

    )

    return result





# ==============================================
#  MAIN FUNCTION
# ==============================================

def run_recommendations(client_ids: list[int] | None = None) -> dict:
    """
    Step 8: For each client, compute sector-level BUY/HOLD/SELL signals
    and generate 1-line descriptions via LLM.
    Returns {client_id: {sector: action}}.
    """
    engine  = init_db(DATABASE_URL)
    Factory = get_session_factory(engine)

    llm = ChatOpenAI(
        model       = "gpt-4o",
        temperature = 0.2,
        api_key     = OPENAI_API_KEY,
        http_client = httpx.Client(verify=False),
    )
    chain = PROMPT | llm | PARSER

    results = {}

    with Factory() as session:

        client_query = session.query(Client).options(
            joinedload(Client.accounts)
            .joinedload(Account.portfolios)
            .joinedload(Portfolio.holdings)
            .joinedload(Holding.security)
            .joinedload(Security.sector),
            joinedload(Client.personal_details),
        )
        if client_ids:
            client_query = client_query.filter(Client.id.in_(client_ids))
        clients = client_query.all()

        if not clients:
            log.warning("No clients found.")
            return {}

        for client in clients:
            log.info(f"\n[Step 8] {client.client_code} – {client.name}")

            # -- Collect sectors from holdings --
            sectors_held: dict[str, float] = {}   # sector_name → total value
            for account in client.accounts:
                for pf in account.portfolios:
                    for h in pf.holdings:
                        sec    = h.security
                        sector = sec.sector.name if sec.sector else None
                        if sector:
                            sectors_held[sector] = (
                                sectors_held.get(sector, 0) + (h.current_value or 0)
                            )

            if not sectors_held:
                log.warning(f"  [{client.client_code}] No holdings found — skipping")
                continue

            log.info(f"  Sectors held: {list(sectors_held.keys())}")

            # -- Fetch outlook drivers ----------
            outlook = session.query(ClientOutlook).filter_by(client_id=client.id).first()
            drivers = json.loads(outlook.drivers or "[]") if outlook else []

            if not drivers:
                log.warning(f"  [{client.client_code}] No outlook drivers — run step 5 first")

            # -- Fetch theme matches ------------
            matches = (
                session.query(ClientThemeMatch)
                .options(joinedload(ClientThemeMatch.theme))
                .filter(ClientThemeMatch.client_id == client.id)
                .all()
            )

            # -- SIGNAL ENGINE: score each sector
            signals = []
            for sector_name in sectors_held:
                sig = compute_signal(sector_name, drivers, matches, session)
                signals.append(sig)
                log.info(
                    f"  {sector_name:<25} -> {sig['action']:<4}  "
                    f"score={sig['signal_score']:+.2f}"
                )

            # -- LLM: generate 1 description per sector (single call)
            personal     = client.personal_details
            constraints  = personal.client_constraints if personal else "None"

            prompt_inputs = {
                "client_name":        client.name,
                "risk_profile":       client.risk_profile or "N/A",
                "constraints":        constraints,
                "sector_signals_text": _build_sector_signals_text(signals),
                "drivers_text":       _build_drivers_text(drivers),
                "themes_text":        _build_themes_text(matches),
                "format_instructions": PARSER.get_format_instructions(),
            }

            descriptions: dict[str, str] = {}
            try:
                result: SectorRecommendationsResult = chain.invoke(prompt_inputs)
                descriptions = {
                    sd.sector_name: sd.description
                    for sd in result.sector_descriptions
                }
            except Exception as e:
                log.error(f"  [{client.client_code}] LLM description failed: {e}")
                # Fallback: use template descriptions
                for sig in signals:
                    descriptions[sig["sector_name"]] = _fallback_description(sig)

            # -- Save to DB --------------------
            _save_sector_recommendations(session, client.id, signals, descriptions)


            # ---------- NEW PART 2 STARTS HERE ----------

            unowned_signals = _compute_unowned_sector_signals(
                session=session,
                drivers=drivers,
                matches=matches,
                owned_sector_names=set(sectors_held.keys()),
            )

            positive_opportunity_signals = [
                signal
                for signal in unowned_signals
                if signal["signal_score"] > BUY_THRESHOLD
            ]

            log.info(
                "[PART 2] Positive Opportunity Sectors (%d): %s",
                len(positive_opportunity_signals),
                ", ".join(
                    s["sector_name"]
                    for s in positive_opportunity_signals
                ) or "None",
            )

            candidate_securities = _get_candidate_securities(session, positive_opportunity_signals)

            log.info( "[PART 2] Candidate Securities:")

            for sec in candidate_securities:
                log.info(
                    "   %-8s %-35s %-20s",
                    sec.ticker,
                    sec.name,
                    sec.sector.name,
                )

            candidate_funds = _get_candidate_funds(positive_opportunity_signals)

            log.info(
                "[PART 2] Candidate Funds:"
            )

            for fund in candidate_funds:
                log.info(
                    "   %-6s %-35s %-20s",
                    fund["fund_id"],
                    fund["fund_name"],
                    fund["sector"],
                )

            if not candidate_securities and not candidate_funds:
                log.info(
                    f"  [{client.client_code}] No investment candidates found."
                )
                continue

            constraints = (
                client.personal_details.client_constraints
                if client.personal_details
                else "None"
            )

            drivers_text = _build_drivers_text(drivers)
            themes_text = _build_themes_text(matches)

            fund_recommendations = _generate_fund_recommendations(
                llm=llm,
                client=client,
                candidate_securities=candidate_securities,
                candidate_funds=candidate_funds,
                positive_opportunity_signals=positive_opportunity_signals,
                drivers_text=drivers_text,
                themes_text=themes_text,
                constraints=constraints
            )

            _save_fund_recommendations(
                session=session,
                client_id=client.id,
                recommendation_result=fund_recommendations
            )

            results[client.id] = {s["sector_name"]: s["action"] for s in signals}
            log.info(f"  [{client.client_code}] {len(signals)} sector recommendation(s) saved.")

    return results


def _fallback_description(sig: dict) -> str:
    """Template-based fallback if LLM call fails."""
    action = sig["action"]
    sector = sig["sector_name"]
    score  = sig["signal_score"]
    if action == "BUY":
        return f"Positive market signals support increasing {sector} exposure."
    elif action == "SELL":
        return f"Negative market signals suggest reducing {sector} allocation."
    else:
        return f"Mixed signals for {sector} — maintain current position."


# ==============================================
#  CLI ENTRY POINT
# ==============================================

if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s  %(levelname)-8s  %(message)s",
    )
    run_recommendations()