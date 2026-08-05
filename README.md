# Finance Intelligence Pipeline

End-to-end pipeline: **Yahoo Finance RSS → Market Events → Trends → Themes → Sector Sentiment**

```
Yahoo Finance RSS
      │
      ▼
┌─────────────────┐
│  Step 1: Ingest │  feedparser + newspaper3k
│                 │  → saves <title>.json to data/articles/YYYY-MM-DD/
│                 │  → persists NewsArticle rows to DB
└────────┬────────┘
         │  new article IDs
         ▼
┌──────────────────────┐
│  Step 2: AI Process  │  OpenAI
│                      │
│  A) Market Events    │  discrete facts per article
│  B) Trends           │  cross-article patterns
│  C) Themes           │  high-level investment narratives
│  D) Sector Tags      │  sector + sentiment per theme
└──────────────────────┘
         │
         ▼
     SQLite / PostgreSQL DB
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialise DB tables
python pipeline.py --init-db

# 3. Seed demo client/portfolio data
python pipeline.py --seed-demo

# 4. Run the pipeline once
python pipeline.py --run-once

# 5. Print report
python pipeline.py --report

# 6. Start scheduled job (every 30 min)
python pipeline.py

Run:
    uvicorn api:app --reload --port 8000

Docs:
    http://localhost:8000/docs
```

---

## Database Schema

### News / Market Intelligence

```
NewsArticle → MarketEvent → MarketEventTrend → Trend → TrendTheme → Theme → ClientThemeMatch → Client
----------------------------
NewsArticle
  id, guid, source_name, title, summary, full_text, url, published_at,
  ingested_at, raw_file_path, is_processed

MarketEvent                         (1 article → many events)
  id, article_id →NewsArticle,
  event_text, event_type, entities

Trend                               (many events → 1 trend, via join table)
  id, name, description, direction, first_seen_at, last_updated

MarketEventTrend                    (join: MarketEvent ↔ Trend)
  market_event_id, trend_id, relevance_score

Theme                               (many trends → 1 theme, via join table)
  id, name, description

TrendTheme                          (join: Trend ↔ Theme)
  trend_id, theme_id, weight

SectorTag                           (sector+sentiment tagged to Theme)
  id, theme_id →Theme, sector_name, sentiment, confidence, rationale
```

### Client / Portfolio

```
Client → Account → Portfolio → Holding → Security → SectorMaster

Client
  id, client_code, name, email, phone, risk_profile

Account
  id, account_number, client_id →Client, account_type, currency

Portfolio
  id, portfolio_code, account_id →Account, name, strategy, total_value

Holding
  id, portfolio_id →Portfolio, security_id →Security,
  quantity, avg_cost, current_value, weight_pct

Security
  id, ticker, name, isin, security_type, exchange, sector_id →SectorMaster,
  last_price

SectorMaster
  id, name, gics_code, description
```

---

## File Storage

```
data/
  raw_feeds/          ← raw XML feed dumps (audit trail)
    yahoo_finance_20260603_143000.xml

  articles/           ← one JSON per article
    2026-06-03/
      nvidia_surpasses_3_trillion__a1b2c3d4.json
      federal_reserve_holds_rates__e5f6g7h8.json
```

---

## Configuration

Edit `config/settings.py`:

| Setting | Default | Description |
|---|---|---|
| `DATABASE_URL` | SQLite | Set to Postgres URL for production |
| `SCHEDULE_INTERVAL_MINUTES` | 30 | How often the pipeline runs |
| `MAX_ARTICLES_PER_RUN` | 10 | Articles processed per run |
| `RSS_SOURCES` | Yahoo Finance | Add/remove feed URLs here |

---

## Output Example

```
INVESTMENT THEMES  →  SECTORS

▸ AI Revolution
  Rapid adoption of generative AI across cloud, devices, and enterprise...
  └ Semiconductors          Positive   [██████████] 95%
  └ Technology              Positive   [████████  ] 82%
  └ Financials              Neutral    [█████     ] 55%

▸ Central Bank Policy Pivot
  Fed signals rate cuts ahead as inflation moderates...
  └ Financials              Mixed      [███████   ] 70%
  └ Real Estate             Positive   [██████    ] 65%
  └ Utilities               Positive   [█████     ] 55%
```

## Step 3 — Client–Theme Matching

    Step 3: Client x Theme
multi-client: step3_match.py loops all clients in one pass — O(clients × themes) — no per-client
API calls needed. Add 100 clients → same code, same speed. Extend seed_clients.py with more rows.

Step 3 closes the loop: it takes the **investment themes and sector tags** extracted in Step 2 and matches them against **each client's actual portfolio holdings** — so every client gets a personalized view of which market themes affect their money, with what sentiment, and how much dollar exposure is behind it.

No new LLM calls are needed here. The match is a pure data join: `Holding → Security → Sector → SectorTag → Theme`.

### Architecture

```
 ┌──────────────┐     ┌──────────────┐     ┌────────────────────┐
 │  Step 1      │ --> │  Step 2      │ --> │  Step 3  ✦ NEW     │
 │  Ingest RSS  │     │  GPT-4o      │     │  Holdings ↔ Themes │
 └──────────────┘     │  Extract     │     └────────────────────┘
                       │  Themes     │
                       └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  SQLite DB   │
                       └──────────────┘
```

## Step 4 — REST API (Read-Only)

Step 4 exposes the data built by Steps 1–3 to a **mid-tier application** over HTTP. The mid-tier app calls these endpoints to read a client's portfolio overview and matched investment themes — it never triggers scraping, AI extraction, or matching itself. That stays the job of `pipeline.py`, run on a schedule.

```
Mid-tier App
     │
     │  HTTP GET
     ▼
┌─────────────────────────┐
│  Step 4: FastAPI        │
│                          │
│  /clients                │
│  /clients/{id}/portfolio │
│  /clients/{id}/themes    │
│  /clients/{id}/overview  │
│  /news/recent            │
└─────────────────────────┘
     │
     │  SQLAlchemy (read-only)
     ▼
   SQLite DB
     ▲
     │  written by
┌──────────┬──────────┬──────────┐
│  Step 1  │  Step 2  │  Step 3  │
│  Ingest  │  AI       │  Match   │
│          │  Process  │          │
└──────────┴──────────┴──────────┘
        orchestrated by pipeline.py
```

## Step 5 — AI Advisor Agent (Market Outlook)

Step 5 is the final layer: it takes everything built in Steps 1–3 — a client's portfolio holdings, their matched investment themes, and recent relevant news — and sends it to **GPT-4o via LangChain** to generate a structured, client-specific market outlook. This is the only step in the pipeline that calls an LLM at this stage; the API (Step 4) only ever reads what Step 5 has already saved.

```
   SQLite DB
   (Steps 1-3 data: portfolio, themes, news)
        │
        ▼
┌─────────────────────────────┐
│  step5_advisor.py  (NEW)    │
│  Builds context:             │
│  - portfolio holdings        │
│  - matched themes            │
│  - recent relevant news      │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  LangChain + GPT-4o          │
│  PydanticOutputParser        │
│  forces structured output    │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  ClientOutlook table (NEW)  │
│  - headline_outlook          │
│  - drivers (JSON)            │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  api.py                      │
│  GET /clients/{id}/outlook  │
│  (read-only)                  │
└─────────────────────────────┘
        │
        ▼
   Mid-tier App
```

## Step 6 — AI Generated Talking Points Agent

Step 6 converts the outputs generated by previous pipeline stages into practical, client-ready conversation guidance for Relationship Managers.
Using the client's profile, meeting history, portfolio data, risk metrics, market outlook, theme exposure, and AI recommendations,
it generates personalized talking points that help Relationship Managers conduct more relevant and engaging client discussions.

The agent produces:

**-Conversation Openers** – Personalized opening statements based on client details and previous discussions.

**-Portfolio Discussion Points** – Portfolio strengths, risks, allocation observations, and discussion opportunities.

**-Product Introductions** – Relevant product and fund introductions based on client context, market outlook, and recommendations.

**-Anticipated Objections** – Predicted client concerns, questions, or objections together with guidance that helps Relationship Managers respond effectively.

```

   SQLite DB
   (Steps 1,2,3,5,7,8 data:
    personal profile,
    meeting history,
    market outlook,
    recommendations,
    portfolio & risk data)

        │
        ▼
┌────────────────────────────────┐
│ step6_generated_talking_points │
│                                │
│ Builds context from:           │
│ - ClientPersonalDetails        │
│ - ClientMeetingSummary         │
│ - ClientOutlook                │
│ - ClientFundRecommendation     │
│ - ClientRiskOverview           │
│ - ClientThemeMatch             │
│ - PortfolioApi                 │
└────────────────────────────────┘
        │
        ▼
┌────────────────────────────────┐
│ OpenAI GPT                     │
│ JSON-structured prompts        │
│ generate:                      │
│                                │
│ - Conversation Openers         │
│ - Portfolio Discussions        │
│ - Product Introductions        |
|  -anticipated_objections       │
└────────────────────────────────┘
        │
        ▼
┌────────────────────────────────┐
│ stores in the ClientAITalking- │
│   Points table                 │
│ - conversation_openers         │
│ - portfolio_discussion         │
│ - product_introduction         │
|  -anticipated_objections       │
└────────────────────────────────┘
        │
        ▼
┌────────────────────────────────┐
│ api.py                         │
│ GET /clients/{id}/talking-     │
│ points                         │
│ (read-only)                    │
└────────────────────────────────┘
        │
        ▼
   Mid-tier App

```

## Step 7 — Client Meeting Summary Agent

Step 7 converts client meeting recordings stored in the meetings/ directory into structured meeting summaries.

The agent transcribes previous client meeting recordings, extracts the most important discussion points, identifies questions raised by the client, and stores a concise summary that can be reused by downstream agents and Relationship Managers.
This creates continuity across client interactions and helps future conversations build on previous discussions.

The agent generates:

**Last Meeting Date** – Date of the previous client meeting.

**Main Discussion Points** – Key topics discussed during the meeting.

**Client Questions** – Questions, concerns, or requests raised by the client.

```

      Meeting Recording Files
   (meetings/{client_code}.mp4)
        │
        ▼
┌─────────────────────────────┐
│ step7_client_meeting_       │
│ summary.py                  │
│                             │
│ Loads meeting recording     │
│ using client_code           │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ OpenAI Audio Transcription  │
│                             │
│ gpt-4o-mini-transcribe      │
│ converts speech to text     │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ LangChain + GPT-4o          │
│ PydanticOutputParser        │
│                             │
│ Extracts:                   │
│ - Discussion Points         │
│ - Client Questions          │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Stores ClientMeetingSummary │
│ table:                      │
│ - last_meeting_date         │
│ - main_discussion_points    │
│ - client_questions          │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ api.py                      │
│ GET /clients/{id}/          │
│ meeting-summary             │
│ (read-only)                 │
└─────────────────────────────┘
        │
        ▼
   Mid-tier App

```

## Step 8 — AI Recommendation Agent

Step 8 is the final recommendation layer of the pipeline.

It combines client portfolio holdings, market outlook, investment themes, and sector sentiment to generate actionable investment recommendations.

The step operates in two phases:

**Part 1 — Sector Recommendation**

For sectors already owned by the client, a deterministic signal engine calculates BUY / HOLD / SELL recommendations using:

-Market Outlook Drivers (Step 5)

-Matched Investment Themes (Step 3)

-Sector Sentiment (Step 2)

GPT-4o then generates concise explanations supporting each sector recommendation.


**Part 2 — Fund Recommendations**

The system evaluates sectors not currently owned by the client to identify attractive diversification opportunities.
Positive sectors are used to generate candidate funds and securities. GPT-4o then selects the most suitable recommendations based on the client's:

-Risk Profile

-Investment Goals

-Preferences

-Constraints

-Market Opportunities


```

   SQLite DB
   (Steps 2-5 data:
    portfolio holdings, outlook drivers, themes,
    sector sentiment,
    client profile)
        │
        ▼
┌─────────────────────────────┐
│ Step 8 - Part 1             │
│ Sector Signal Engine        │
│                             │
│ Uses:                       │
│ - Holdings                  │
│ - ClientOutlook             │
│ - ClientThemeMatch          │
│ - SectorTag                 │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ calculate Score             │
│                             │
│ Calculates:                 │
│ - Driver Signal             │
│ - Theme Signal              │
│ - Sector Sentiment Signal   │
│                             │
│ Produces BUY/HOLD/SELL      │
│ for owned sectors           │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ LangChain + GPT-4o          │
│ PydanticOutputParser        │
│                             │
│ Generates sector-level      │
│ recommendation description   │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ stores in table-            |
| ClientSectorRecommendation,  │
│                             │
│ - sector_name               │
│ - action                    │
│ - signal_score              │
│ - description               │
└─────────────────────────────┘
 
   Part 2 - New Funds Recommendation
        │
        ▼
┌─────────────────────────────┐
│ Unowned Sectors Analysis    │
│                             │
│ Uses:                       │
│ - ClientOutlook             │
│ - ClientThemeMatch          │
│ - SectorTag                 │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│Calculate Scoring            │
│                             │
│ Calculates:                 │
│ - Driver Signal             │
│ - Theme Signal              │
│ - Sector Sentiment Signal   │
│                             │
│ Produces BUY/HOLD/SELL      │
│ for unowned sectors         │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Positive Opportunity        │
│ Sectors                     │
│                             │
│ BUY sectors only            │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ Fetch Funds/Securities from │
│ Fund universe and Security  │
│ table for BUY sectors       │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ LangChain + GPT-4o          │
│ PydanticOutputParser        │
│                             │
│ Selects final fund or       │
│ security recommendations    │
│                             │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ stores in                   |
| ClientFundRecommendation    │
│ Table:                      |
|                             │
│ - mifid_suitability         │
│ - portfolio_rationale       │
│ - recommendations           │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ api.py                      │
│ GET /clients/{id}/          │
│ recommendations             │
│ (read-only)                 │
└─────────────────────────────┘
        │
        ▼
   Mid-tier App
```
 
 
