"""
step3_match.py – Match client holdings to AI-extracted investment themes.

Logic
-----
For every client:
  1. Load all holdings → securities → sectors
  2. Load all themes → sector_tags
  3. If holding's sector matches a SectorTag's sector_name → record a match
  4. Aggregate exposure (value + %) across all holdings that hit the same theme
  5. Upsert into ClientThemeMatch

Multi-client: all clients processed in a single DB session — no per-client API calls.
"""

import json
import logging
from datetime import datetime
from sqlalchemy.orm import joinedload

from models import (
    get_session_factory, init_db,
    Client, Account, Portfolio, Holding, Security, SectorMaster,
    Theme, SectorTag, ClientThemeMatch, SentimentEnum,
)
from config.settings import DATABASE_URL

log = logging.getLogger("step3_match")


def run_matching(client_ids: list[int] | None = None) -> dict:
    """
    Match all (or specified) clients' holdings to current themes.

    Returns a summary dict: {client_id: [matched theme names]}
    """
    engine = init_db(DATABASE_URL)
    Session = get_session_factory(engine)
    results = {}

    with Session() as session:
        # --- Load all themes + their sector tags once (shared across all clients) ---
        themes = (
            session.query(Theme)
            .options(joinedload(Theme.sector_tags))
            .all()
        )
        if not themes:
            log.warning("No themes found. Run step 2 first.")
            return {}

        # Build a lookup: sector_name (lowercase) -> list of (theme, SectorTag)
        sector_to_theme_tags: dict[str, list[tuple[Theme, SectorTag]]] = {}
        for theme in themes:
            for tag in theme.sector_tags:
                key = tag.sector_name.lower().strip()
                sector_to_theme_tags.setdefault(key, []).append((theme, tag))

        log.info(f"Loaded {len(themes)} themes covering "
                 f"{len(sector_to_theme_tags)} distinct sectors.")

        # --- Load clients ---
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
            log.warning("No clients found. Run --seed-demo first.")
            return {}

        log.info(f"Processing {len(clients)} client(s)...")

        for client in clients:
            matched_themes: dict[int, dict] = {}  # theme_id -> aggregation bucket

            # Gather all holdings across all accounts + portfolios
            total_portfolio_value = 0.0
            all_holdings = []
            for account in client.accounts:
                for portfolio in account.portfolios:
                    total_portfolio_value += portfolio.total_value or 0.0
                    all_holdings.extend(portfolio.holdings)

            for holding in all_holdings:
                sec = holding.security
                if not sec or not sec.sector:
                    continue

                sector_name = sec.sector.name.lower().strip()
                if sector_name not in sector_to_theme_tags:
                    continue  # holding's sector not in any theme

                for (theme, tag) in sector_to_theme_tags[sector_name]:
                    bucket = matched_themes.setdefault(theme.id, {
                        "theme": theme,
                        "matched_sectors": set(),
                        "exposure_value": 0.0,
                        "best_sentiment": None,
                        "best_confidence": 0.0,
                    })
                    bucket["matched_sectors"].add(sec.sector.name)
                    bucket["exposure_value"] += holding.current_value or 0.0
                    # Keep the highest-confidence tag's sentiment
                    if tag.confidence > bucket["best_confidence"]:
                        bucket["best_confidence"] = tag.confidence
                        bucket["best_sentiment"] = tag.sentiment

            # Upsert ClientThemeMatch rows
            client_matched_theme_names = []
            for theme_id, bucket in matched_themes.items():
                exposure_pct = (
                    (bucket["exposure_value"] / total_portfolio_value * 100)
                    if total_portfolio_value > 0 else 0.0
                )
                existing = (
                    session.query(ClientThemeMatch)
                    .filter_by(client_id=client.id, theme_id=theme_id)
                    .first()
                )
                if existing:
                    existing.matched_at      = datetime.utcnow()
                    existing.matched_sectors = json.dumps(sorted(bucket["matched_sectors"]))
                    existing.exposure_value  = bucket["exposure_value"]
                    existing.exposure_pct    = exposure_pct
                    existing.sentiment       = bucket["best_sentiment"]
                    existing.confidence      = bucket["best_confidence"]
                else:
                    session.add(ClientThemeMatch(
                        client_id       = client.id,
                        theme_id        = theme_id,
                        matched_sectors = json.dumps(sorted(bucket["matched_sectors"])),
                        exposure_value  = bucket["exposure_value"],
                        exposure_pct    = exposure_pct,
                        sentiment       = bucket["best_sentiment"],
                        confidence      = bucket["best_confidence"],
                    ))
                client_matched_theme_names.append(bucket["theme"].name)

            session.commit()
            results[client.id] = client_matched_theme_names
            log.info(f"  [{client.client_code}] {client.name} -> "
                     f"{len(client_matched_theme_names)} theme(s) matched: "
                     f"{client_matched_theme_names}")

    return results