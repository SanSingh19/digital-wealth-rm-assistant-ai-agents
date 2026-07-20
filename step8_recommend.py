"""
step6_recommend.py – Step 8: AI Fund Recommendation Agent

Goal: Recommend top 3 funds for each client, scored, ranked, with action + priority.

Frontend output format:
  MiFID II: All Pass – Suitability validated against <Risk Profile>
  <ACTION>  <Fund Name>  <Priority>
  <Rationale>

Agent Design
────────────
  INPUTS (from DB)
    - Client profile, constraints, investment goals, age, profession
    - Holdings: sectors, weights, P&L
    - Asset class preference bandwidths
    - Theme matches + market outlook drivers (Increase/Decrease/Neutral)
    - Risk overview: concentration, sharpe, VaR, drawdown

  TOOLS (deterministic Python)
    - filter_funds()  : hard filter on risk + preference bandwidths
    - score_fund()    : 5-dimension scoring (no LLM)

  LLM (GPT-4o via LangChain)
    - Picks top 3 from pre-scored candidates
    - Assigns action (BUY/HOLD/SWITCH/SELL) and priority (High/Medium/Low)
    - Writes specific rationale per recommendation
    - Generates MiFID II suitability statement
    - Writes overall portfolio rationale

  OUTPUT → client_fund_recommendations table → api.py
"""

import json
import logging
import ssl
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

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
    ClientRiskOverview, ClientPreference,
    ClientFundRecommendation,
)

log = logging.getLogger("step6_recommend")


# ==============================================
#  FUND UNIVERSE
#  Aligned with seed_clients.py security types
# ==============================================

FUND_UNIVERSE = [
    {
        "fund_id":          "F001",
        "fund_name":        "European AI & Semiconductor ETF",
        "category":         "Technology",
        "security_type":    "EQUITY",
        "sector_weights":   {"Semiconductors": 55, "Technology": 45},
        "return_1yr":       38.5,
        "category_avg_1yr": 28.0,
        "expense_ratio":    0.35,
        "risk_rating":      "Aggressive",
        "currency":         "EUR",
        "description":      "Tracks European AI chip makers and software leaders including ASML and NVDA.",
    },
    {
        "fund_id":          "F002",
        "fund_name":        "EU Clean Energy Transition Fund",
        "category":         "Renewable Energy",
        "security_type":    "ALTERNATIVES",
        "sector_weights":   {"Renewable Energy": 70, "Technology": 30},
        "return_1yr":       18.2,
        "category_avg_1yr": 14.0,
        "expense_ratio":    0.55,
        "risk_rating":      "Moderate",
        "currency":         "EUR",
        "description":      "ESG-aligned fund investing in solar, wind, and EU green infrastructure.",
    },
    {
        "fund_id":          "F003",
        "fund_name":        "Euro Government Bond Fund",
        "category":         "Fixed Income",
        "security_type":    "FIXED_INCOME",
        "sector_weights":   {"Financials": 100},
        "return_1yr":       5.8,
        "category_avg_1yr": 5.0,
        "expense_ratio":    0.18,
        "risk_rating":      "Conservative",
        "currency":         "EUR",
        "description":      "High-quality European sovereign bonds for capital preservation.",
    },
    {
        "fund_id":          "F004",
        "fund_name":        "European Real Estate Income ETF",
        "category":         "Real Estate",
        "security_type":    "REAL_ESTATE",
        "sector_weights":   {"Real Estate": 100},
        "return_1yr":       14.8,
        "category_avg_1yr": 11.0,
        "expense_ratio":    0.42,
        "risk_rating":      "Moderate",
        "currency":         "EUR",
        "description":      "Diversified European REITs and property income funds.",
    },
    {
        "fund_id":          "F005",
        "fund_name":        "ESG Small Cap Innovation Fund",
        "category":         "ESG Alternatives",
        "security_type":    "ALTERNATIVES",
        "sector_weights":   {"Renewable Energy": 50, "Technology": 30, "Financials": 20},
        "return_1yr":       22.3,
        "category_avg_1yr": 16.0,
        "expense_ratio":    0.65,
        "risk_rating":      "Aggressive",
        "currency":         "EUR",
        "description":      "High-growth ESG small-caps benefiting from EU taxonomy expansion.",
    },
    {
        "fund_id":          "F006",
        "fund_name":        "Short Duration Green Bond Fund",
        "category":         "Fixed Income",
        "security_type":    "FIXED_INCOME",
        "sector_weights":   {"Financials": 60, "Renewable Energy": 40},
        "return_1yr":       6.5,
        "category_avg_1yr": 5.0,
        "expense_ratio":    0.22,
        "risk_rating":      "Conservative",
        "currency":         "EUR",
        "description":      "Short-duration green bonds — lower rate sensitivity, ESG-compliant.",
    },
    {
        "fund_id":          "F007",
        "fund_name":        "European Dividend Leaders Fund",
        "category":         "Equity Income",
        "security_type":    "EQUITY",
        "sector_weights":   {"Financials": 35, "Technology": 30, "Consumer Discretionary": 35},
        "return_1yr":       12.1,
        "category_avg_1yr": 10.0,
        "expense_ratio":    0.40,
        "risk_rating":      "Moderate",
        "currency":         "EUR",
        "description":      "Financially strong European companies with consistent dividend growth.",
    },
    {
        "fund_id":          "F008",
        "fund_name":        "Money Market Plus Fund",
        "category":         "Liquidity",
        "security_type":    "LIQUIDITY",
        "sector_weights":   {"Financials": 100},
        "return_1yr":       3.8,
        "category_avg_1yr": 3.5,
        "expense_ratio":    0.10,
        "risk_rating":      "Conservative",
        "currency":         "EUR",
        "description":      "Enhanced money market — slightly better yield than standard cash.",
    },
    {
        "fund_id":          "F009",
        "fund_name":        "Global Technology Growth Fund",
        "category":         "Technology",
        "security_type":    "EQUITY",
        "sector_weights":   {"Technology": 60, "Semiconductors": 40},
        "return_1yr":       44.2,
        "category_avg_1yr": 28.0,
        "expense_ratio":    0.50,
        "risk_rating":      "Aggressive",
        "currency":         "EUR",
        "description":      "Global AI, cloud, and semiconductor leaders — MSFT, NVDA, ASML focus.",
    },
    {
        "fund_id":          "F010",
        "fund_name":        "Investment Grade Corporate Bond Portfolio",
        "category":         "Fixed Income",
        "security_type":    "FIXED_INCOME",
        "sector_weights":   {"Financials": 70, "Technology": 30},
        "return_1yr":       7.2,
        "category_avg_1yr": 5.5,
        "expense_ratio":    0.28,
        "risk_rating":      "Moderate",
        "currency":         "EUR",
        "description":      "Diversified investment-grade corporate bonds — better yield than govts.",
    },
]

# Risk level for filter logic
RISK_ORDER = {"Conservative": 1, "Moderate": 2, "Aggressive": 3}

# MiFID II risk profile label mapping
MIFID_PROFILE_MAP = {
    "Conservative": "Conservative (RP2)",
    "Moderate":     "Moderately Offensive (RP4)",
    "Aggressive":   "Aggressive (RP5)",
}


# ==============================================
#  PYDANTIC OUTPUT SCHEMA
# ==============================================

class ScoreBreakdown(BaseModel):
    theme_alignment: int = Field(description="0-10: fund sectors align with Increase-status drivers")
    diversification: int = Field(description="0-10: fund reduces existing concentration")
    performance:     int = Field(description="0-10: 1yr return vs category average")
    cost_efficiency: int = Field(description="0-10: lower expense ratio = higher score")
    risk_match:      int = Field(description="0-10: fund risk rating matches client profile")


class FundRecommendation(BaseModel):
    rank:   int = Field(description="1, 2, or 3")
    fund_id: str = Field(description="Fund identifier e.g. F001")
    fund_name: str = Field(description="Fund display name")

    action: Literal["BUY", "HOLD", "SWITCH", "SELL"] = Field(
        description=(
            "BUY: add this new fund to the portfolio. "
            "HOLD: maintain an existing position (reference the ticker). "
            "SWITCH: rotate from one existing allocation into this fund. "
            "SELL: exit an existing position."
        )
    )

    priority: Literal["High", "Medium", "Low"] = Field(
        description=(
            "High: directly addresses an Increase driver or fills a clear portfolio gap. "
            "Medium: complementary or risk-management focused. "
            "Low: defensive or cautionary action."
        )
    )

    total_score:              int   = Field(description="Weighted total score out of 100")
    score_breakdown:          ScoreBreakdown
    rationale:                str   = Field(
        description=(
            "2 sentences max. Reference the client's actual tickers, sectors, constraints, "
            "and outlook drivers. Be specific — e.g. 'Aligns with ESG conviction + taxonomy "
            "expansion tailwind. Fills small-cap gap in portfolio.'"
        )
    )
    suggested_allocation_pct: float = Field(
        description="Suggested % of total portfolio to allocate (5-20%)"
    )


class FundRecommendationResult(BaseModel):
    mifid_suitability: str = Field(
        description=(
            "One-line MiFID II suitability statement. "
            "Format: 'All Pass – Suitability validated against <risk profile label>'. "
            "Example: 'All Pass – Suitability validated against Moderately Offensive (RP4)'"
        )
    )
    recommendations: list[FundRecommendation] = Field(
        description="Exactly 3 recommendations ranked 1 to 3"
    )
    portfolio_rationale: str = Field(
        description=(
            "1 paragraph explaining the overall recommended fund mix in the context of "
            "the client's current portfolio, constraints, and market outlook."
        )
    )


PARSER = PydanticOutputParser(pydantic_object=FundRecommendationResult)

PROMPT = ChatPromptTemplate.from_template(
    """You are a senior wealth management advisor. Recommend exactly 3 funds for this
client from the pre-scored list. Base all output strictly on the data provided below.

AGENT REASONING INSTRUCTIONS
──────────────────────────────
1. Respect client constraints — they are hard rules, not preferences.
2. Prioritise funds whose sectors align with Increase-status market outlook drivers.
3. Avoid funds that increase concentration in already overweight sectors.
4. Never recommend a fund with higher risk than the client allows.
5. Use pre-computed scores as your primary ranking signal.
6. For action:
   - BUY  → recommending a new fund to add
   - HOLD → an existing holding worth maintaining (name the ticker)
   - SWITCH → rotating from an existing allocation into this fund (name what you're switching from)
   - SELL → exiting a current position
7. For priority: High if directly addresses Increase driver or clear gap,
   Medium if complementary, Low if defensive.
8. Rationale must be 2 sentences max — punchy, specific, reference actual data.
9. For mifid_suitability use this client's risk profile: {risk_profile}
   Map to: Conservative→"Conservative (RP2)", Moderate→"Moderately Offensive (RP4)",
   Aggressive→"Aggressive (RP5)"
   Format: "All Pass – Suitability validated against <label>"

CLIENT PROFILE
───────────────
Name:             {client_name}
Age:              {age}
Profession:       {profession}
Risk Profile:     {risk_profile}
Investment Goals: {investment_goals}
Service Model:    {service_model}

CLIENT CONSTRAINTS (hard rules)
─────────────────────────────────
{constraints_text}

CURRENT HOLDINGS (ticker | sector | weight% | P&L)
────────────────────────────────────────────────────
{holdings_text}

ASSET CLASS PREFERENCES (allowed bandwidths)
─────────────────────────────────────────────
{preferences_text}

RISK OVERVIEW
──────────────
{risk_overview_text}

MARKET OUTLOOK DRIVERS (Increase / Decrease / Neutral)
───────────────────────────────────────────────────────
{drivers_text}

MATCHED INVESTMENT THEMES
──────────────────────────
{themes_text}

PRE-SCORED FUND OPTIONS (top 5 by score, already filtered)
───────────────────────────────────────────────────────────
{scored_funds_text}

{format_instructions}
"""
)


# ==============================================
#  TOOL 1: SCORE FUND (deterministic Python)
# ==============================================

def score_fund(fund: dict, client_context: dict) -> dict:
    """
    Pure Python scoring — no LLM.
    5 dimensions, weighted total out of 100.
    """
    scores = {}

    # 1. THEME ALIGNMENT
    increase_sectors = set(client_context.get("increase_sectors", []))
    decrease_sectors = set(client_context.get("decrease_sectors", []))
    fund_sectors     = set(fund["sector_weights"].keys())

    hits = len(fund_sectors & increase_sectors)
    miss = len(fund_sectors & decrease_sectors)
    scores["theme_alignment"] = max(0, min(10, (hits * 3) - (miss * 2) + 5))

    # 2. DIVERSIFICATION
    overweight  = set(client_context.get("overweight_sectors", []))
    overlap_pct = len(fund_sectors & overweight) / len(fund_sectors) if fund_sectors else 0
    scores["diversification"] = round(10 - (overlap_pct * 10))

    # 3. PERFORMANCE vs category average
    diff = fund["return_1yr"] - fund["category_avg_1yr"]
    if diff >= 10:   scores["performance"] = 10
    elif diff >= 5:  scores["performance"] = 8
    elif diff >= 2:  scores["performance"] = 6
    elif diff >= 0:  scores["performance"] = 5
    else:            scores["performance"] = max(0, 5 + round(diff))

    # 4. COST EFFICIENCY
    er = fund["expense_ratio"]
    if er <= 0.20:   scores["cost_efficiency"] = 10
    elif er <= 0.35: scores["cost_efficiency"] = 8
    elif er <= 0.50: scores["cost_efficiency"] = 6
    elif er <= 0.65: scores["cost_efficiency"] = 4
    else:            scores["cost_efficiency"] = 2

    # 5. RISK MATCH
    client_lvl = RISK_ORDER.get(client_context.get("risk_profile", "Moderate"), 2)
    fund_lvl   = RISK_ORDER.get(fund["risk_rating"], 2)
    scores["risk_match"] = {0: 10, 1: 6, 2: 2}.get(abs(client_lvl - fund_lvl), 0)

    # WEIGHTED TOTAL
    weights = {
        "theme_alignment": 0.30,
        "diversification": 0.25,
        "performance":     0.20,
        "cost_efficiency": 0.15,
        "risk_match":      0.10,
    }
    scores["total_score"] = round(sum(scores[k] * weights[k] * 10 for k in weights))
    return scores


# ==============================================
#  TOOL 2: FILTER FUND UNIVERSE
# ==============================================

def filter_funds(funds: list[dict], client_context: dict) -> list[dict]:
    """
    Hard filters:
    1. Fund risk must not exceed client risk profile
    2. Fund security_type must be within client preference bandwidth (max > 0)
    3. Exclude funds where ALL sectors are in Decrease-status drivers
    """
    client_risk_lvl  = RISK_ORDER.get(client_context["risk_profile"], 2)
    pref_map         = client_context.get("preference_bandwidths", {})
    decrease_sectors = set(client_context.get("decrease_sectors", []))

    eligible = []
    for f in funds:
        if RISK_ORDER.get(f["risk_rating"], 2) > client_risk_lvl:
            continue
        pref = pref_map.get(f.get("security_type", ""), {})
        if pref.get("max", 100) == 0:
            continue
        fund_sectors = set(f["sector_weights"].keys())
        if fund_sectors and fund_sectors.issubset(decrease_sectors):
            continue
        eligible.append(f)

    return eligible


# ==============================================
#  TOOL 3: BUILD CLIENT CONTEXT
# ==============================================

def _build_client_context(
    client,
    matches: list,
    outlook,
    personal_details,
    risk_overview,
    preferences: list,
) -> dict:

    holdings      = []
    sector_totals: dict[str, float] = {}
    total_value   = 0.0

    for account in client.accounts:
        for pf in account.portfolios:
            for h in pf.holdings:
                sec    = h.security
                sector = sec.sector.name if sec.sector else "Unknown"
                value  = h.current_value or 0.0
                pnl    = ((sec.last_price or 0) - (h.avg_cost or 0)) * h.quantity
                holdings.append({
                    "ticker": sec.ticker,
                    "name":   sec.name,
                    "sector": sector,
                    "stype":  sec.security_type,
                    "value":  value,
                    "weight": h.weight_pct or 0,
                    "pnl":    pnl,
                })
                sector_totals[sector] = sector_totals.get(sector, 0) + value
                total_value += value

    overweight = [
        s for s, v in sector_totals.items()
        if total_value > 0 and (v / total_value) > 0.20
    ]

    pref_map = {
        p.security_type: {"min": p.bandwidth_min, "max": p.bandwidth_max}
        for p in preferences
    }

    increase_sectors: list[str] = []
    decrease_sectors: list[str] = []
    drivers_data: list[dict]    = []

    if outlook and outlook.drivers:
        for d in json.loads(outlook.drivers or "[]"):
            status = d.get("status", "Neutral")
            drivers_data.append(d)
            matched = _infer_sectors_from_title(d.get("title", "").lower())
            if status == "Increase":
                increase_sectors.extend(matched)
            elif status == "Decrease":
                decrease_sectors.extend(matched)

    return {
        "risk_profile":          client.risk_profile or "Moderate",
        "age":                   client.age,
        "profession":            client.profession,
        "investment_goals":      client.investment_goals,
        "service_model":         client.service_model,
        "constraints":           personal_details.client_constraints if personal_details else "",
        "holdings":              holdings,
        "overweight_sectors":    overweight,
        "sector_totals":         sector_totals,
        "total_value":           total_value,
        "preference_bandwidths": pref_map,
        "increase_sectors":      list(set(increase_sectors)),
        "decrease_sectors":      list(set(decrease_sectors)),
        "drivers":               drivers_data,
        "headline_outlook":      outlook.headline_outlook if outlook else "",
        "themes": [
            {
                "name":         m.theme.name,
                "exposure_pct": m.exposure_pct,
                "sentiment":    m.sentiment.value if m.sentiment else "N/A",
            }
            for m in matches
        ],
        "risk_overview": {
            "concentration_pct":   risk_overview.concentration_pct   if risk_overview else "N/A",
            "concentration_asset": risk_overview.concentration_asset if risk_overview else "N/A",
            "sharpe_ratio":        risk_overview.sharpe_ratio        if risk_overview else "N/A",
            "value_at_risk":       risk_overview.value_at_risk       if risk_overview else "N/A",
            "max_drawdown":        risk_overview.max_drawdown        if risk_overview else "N/A",
        },
    }


def _infer_sectors_from_title(title: str) -> list[str]:
    mapping = {
        "energy":        "Energy",
        "oil":           "Energy",
        "tech":          "Technology",
        "technology":    "Technology",
        "semiconductor": "Semiconductors",
        "chip":          "Semiconductors",
        "nvidia":        "Semiconductors",
        "asml":          "Semiconductors",
        "ai":            "Technology",
        "cloud":         "Technology",
        "bank":          "Financials",
        "financ":        "Financials",
        "rate":          "Financials",
        "bond":          "Financials",
        "renewable":     "Renewable Energy",
        "solar":         "Renewable Energy",
        "esg":           "Renewable Energy",
        "green":         "Renewable Energy",
        "real estate":   "Real Estate",
        "reit":          "Real Estate",
        "consumer":      "Consumer Discretionary",
    }
    return list({sector for kw, sector in mapping.items() if kw in title})


# ==============================================
#  PROMPT BUILDERS
# ==============================================

def _build_holdings_text(ctx: dict) -> str:
    lines = []
    for h in ctx["holdings"]:
        sign = "+" if h["pnl"] >= 0 else ""
        lines.append(
            f"- {h['ticker']} ({h['name']}) | {h['sector']} | "
            f"{h['weight']:.1f}% | P&L {sign}€{h['pnl']:,.0f}"
        )
    return "\n".join(lines) or "No holdings."


def _build_preferences_text(ctx: dict) -> str:
    return "\n".join(
        f"- {stype}: {v['min']}% – {v['max']}%"
        for stype, v in ctx["preference_bandwidths"].items()
    ) or "No preferences defined."


def _build_risk_text(ctx: dict) -> str:
    r = ctx["risk_overview"]
    return (
        f"- Concentration: {r['concentration_pct']}% in {r['concentration_asset']}\n"
        f"- Sharpe Ratio:  {r['sharpe_ratio']}\n"
        f"- Value at Risk: €{r['value_at_risk']}\n"
        f"- Max Drawdown:  {r['max_drawdown']}%"
    )


def _build_drivers_text(ctx: dict) -> str:
    lines = [
        f"- [{d.get('status','Neutral')}] {d.get('title','')}: {d.get('commentary','')}"
        for d in ctx["drivers"]
    ]
    return "\n".join(lines) if lines else ctx.get("headline_outlook", "No outlook available.")


def _build_themes_text(ctx: dict) -> str:
    return "\n".join(
        f"- {t['name']}: exposure={t['exposure_pct']:.1f}%, sentiment={t['sentiment']}"
        for t in ctx["themes"]
    ) or "No themes matched."


def _build_scored_funds_text(scored_funds: list[dict]) -> str:
    lines = []
    for sf in scored_funds:
        f      = sf["fund"]
        scores = sf["scores"]
        sectors = ", ".join(f"{s}: {w}%" for s, w in f["sector_weights"].items())
        lines.append(
            f"\n[{f['fund_id']}] {f['fund_name']}"
            f"\n  Type:          {f['security_type']}"
            f"\n  Sectors:       {sectors}"
            f"\n  1yr Return:    {f['return_1yr']}% (category avg: {f['category_avg_1yr']}%)"
            f"\n  Expense Ratio: {f['expense_ratio']}%"
            f"\n  Risk Rating:   {f['risk_rating']}"
            f"\n  SCORES → Total: {scores['total_score']}/100 | "
            f"Theme: {scores['theme_alignment']}/10 | "
            f"Divs: {scores['diversification']}/10 | "
            f"Perf: {scores['performance']}/10 | "
            f"Cost: {scores['cost_efficiency']}/10 | "
            f"Risk: {scores['risk_match']}/10"
            f"\n  Description:   {f['description']}"
        )
    return "\n".join(lines)


# ==============================================
#  DB SAVE
# ==============================================

def _save_recommendations(
    session: Session,
    client_id: int,
    result: FundRecommendationResult,
):
    recs_json = json.dumps([r.model_dump() for r in result.recommendations])
    existing  = session.query(ClientFundRecommendation).filter_by(client_id=client_id).first()

    if existing:
        existing.mifid_suitability   = result.mifid_suitability
        existing.recommendations     = recs_json
        existing.portfolio_rationale = result.portfolio_rationale
        existing.generated_at        = datetime.utcnow()
    else:
        session.add(ClientFundRecommendation(
            client_id           = client_id,
            mifid_suitability   = result.mifid_suitability,
            recommendations     = recs_json,
            portfolio_rationale = result.portfolio_rationale,
        ))
    session.commit()


# ==============================================
#  MAIN AGENT FUNCTION
# ==============================================

def run_recommendations(client_ids: list[int] | None = None) -> dict:
    """
    Step 6: Score + rank funds per client, generate action/priority/rationale.
    Returns {client_id: [top 3 fund names]}.
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
            joinedload(Client.risk_overview),
            joinedload(Client.preferences),
        )
        if client_ids:
            client_query = client_query.filter(Client.id.in_(client_ids))
        clients = client_query.all()

        if not clients:
            log.warning("No clients found.")
            return {}

        for client in clients:
            log.info(f"\n[Step 6] {client.client_code} – {client.name}")

            matches     = (
                session.query(ClientThemeMatch)
                .options(joinedload(ClientThemeMatch.theme))
                .filter(ClientThemeMatch.client_id == client.id)
                .order_by(ClientThemeMatch.exposure_pct.desc())
                .all()
            )
            outlook     = session.query(ClientOutlook).filter_by(client_id=client.id).first()
            personal    = client.personal_details
            risk_ov     = session.query(ClientRiskOverview).filter_by(client_id=client.id).first()
            preferences = session.query(ClientPreference).filter_by(client_id=client.id).all()

            ctx      = _build_client_context(client, matches, outlook, personal, risk_ov, preferences)
            eligible = filter_funds(FUND_UNIVERSE, ctx)
            log.info(f"  {len(eligible)} funds eligible after filtering")

            if not eligible:
                log.warning(f"  No eligible funds for {client.client_code} — skipping")
                continue

            scored = sorted(
                [{"fund": f, "scores": score_fund(f, ctx)} for f in eligible],
                key=lambda x: x["scores"]["total_score"],
                reverse=True,
            )

            top5 = scored[:5]

            prompt_inputs = {
                "client_name":         client.name,
                "age":                 ctx["age"] or "N/A",
                "profession":          ctx["profession"] or "N/A",
                "risk_profile":        ctx["risk_profile"],
                "investment_goals":    ctx["investment_goals"] or "N/A",
                "service_model":       ctx["service_model"] or "N/A",
                "constraints_text":    ctx["constraints"] or "No specific constraints.",
                "holdings_text":       _build_holdings_text(ctx),
                "preferences_text":    _build_preferences_text(ctx),
                "risk_overview_text":  _build_risk_text(ctx),
                "drivers_text":        _build_drivers_text(ctx),
                "themes_text":         _build_themes_text(ctx),
                "scored_funds_text":   _build_scored_funds_text(top5),
                "format_instructions": PARSER.get_format_instructions(),
            }

            try:
                result: FundRecommendationResult = chain.invoke(prompt_inputs)
            except Exception as e:
                log.error(f"  [{client.client_code}] LLM call failed: {e}")
                continue

            log.info(f"  [{client.client_code}] MiFID: {result.mifid_suitability}")
            for rec in result.recommendations:
                log.info(
                    f"    #{rec.rank} [{rec.action}] {rec.fund_name} "
                    f"| Priority: {rec.priority} | Score: {rec.total_score}/100"
                )

            _save_recommendations(session, client.id, result)
            results[client.id] = [r.fund_name for r in result.recommendations]

    return results


# ==============================================
#  CLI ENTRY POINT
# ==============================================

if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s  %(levelname)-8s  %(message)s",
    )
    run_recommendations()