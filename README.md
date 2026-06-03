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
│  Step 2: AI Process  │  Claude Sonnet
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

# 2. Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Initialise DB tables
python pipeline.py --init-db

# 4. Seed demo client/portfolio data
python pipeline.py --seed-demo

# 5. Run the pipeline once
python pipeline.py --run-once

# 6. Print report
python pipeline.py --report

# 7. Start scheduled job (every 30 min)
python pipeline.py
```

---

## Database Schema

### News / Market Intelligence

```
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
