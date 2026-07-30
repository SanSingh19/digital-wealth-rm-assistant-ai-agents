"""
    step6_generated_talking_points.py - Step 6 :Generates AI-driven sales and engagement talking points to help
    representatives conduct meaningful customer conversations.

    This class is responsible for creating the following content:

    - conversationOpeners:
      Personalized opening statements designed to initiate engaging
      and relevant customer discussions.

    - portfolioDiscussion:
      Key discussion points highlighting portfolio strengths, business
      value, capabilities, and alignment with customer needs.

    - productIntroduction:
      Concise and impactful product introductions that communicate
      features, benefits, and value propositions.

    - anticipatedObjections:
      Predicted customer concerns, questions, or objections along with
      guidance for addressing them effectively.

    The generated content leverages customer context, business insights,
    and AI-powered recommendations to improve conversation quality,
    customer engagement, and sales effectiveness.
    """

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any
from portfolio_api import PortfolioApi

import httpx
from openai import OpenAI

from config.settings import DATABASE_URL, OPENAI_API_KEY, OPENAI_MODEL
from models import (
    Client,
    ClientAITalkingPoints,
    ClientMeetingSummary,
    ClientPersonalDetails,
    ClientRiskOverview,
    ClientThemeMatch,
    Account,
    Portfolio,
    Holding,
    Security,
    get_session_factory,
    init_db,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))

log = logging.getLogger("step6_generated_talking_points")


def _truncate(text: Any, limit: int = 180) -> str:
    value = str(text or "")
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _summarize_client(client_details: Any, meeting: Any) -> str:
    meeting_summary = meeting.main_discussion_points if meeting else "No Meeting Summary"
    return (
        f"client_id={client_details.id}, dob={client_details.date_of_Birth}, "
        f"marital_status={client_details.marital_status}, kids={client_details.kids_details}, "
        f"hobbies={_truncate(client_details.hobbies)}, other={_truncate(client_details.other)}, "
        f"meeting_summary={_truncate(meeting_summary)}"
    )


SYSTEM_CONVERSATION_OPENERS = """
You are a Relationship Manager AI Assistant.
Your role is to create personalized conversation openers for clients using their personal details, interests, and previous meeting conversations.
Don't ask more sensible personal topics.
Respond ONLY with valid JSON – no preamble, no markdown fences.
""".strip()

SYSTEM_PORTFOLIO_DISCUSSION = """
You are an experienced Wealth Relationship Manager.

Generate portfolio discussion points for the relationship manager.

Return ONLY valid JSON.
""".strip()

PROMPT_CONVERSATION_OPENERS = """
Client Details and Last Meeting Summary:

{client_block}

Generate top 2 personalized conversation openers based on the client's profile and previous discussions.


Rules:
- Professional and relationship-focused.
- Maintain a warm, professional, and welcoming tone on first contact.
- Focus on building rapport and trust.
- First opener should be a warm greeting and personal details .
- Second opener should use the last meeting summary as the starting point for the conversation.
- Reference relevant topics discussed previously when appropriate.
- Maximum two topics per opener.
- No sensitive or intrusive questions.
- No assumptions.
- Keep responses concise.
- Do not start every opener with a greeting.
- If a greeting is used, use it only in the first opener.
- Ensure each opener has a distinct opening style and does not repeat salutation phrases.

Respond ONLY with valid JSON.


{{
  "client_id": "<use the current client's id from the client block>",
  "conversationOpeners": ["string"]
}}
""".strip()

PROMPT_PORTFOLIO_DISCUSSION = """
Client Information

{portfolio_context}

Generate ONLY TWO portfolio discussion points.

Discussion Point 1
------------------
Decide automatically.

IF every asset allocation is within its recommended bandwidth:
- Write a Positive Portfolio Highlight.
- Mention portfolio performance or diversification.
- Mention strong holdings only if supported by the data.
- Do NOT recommend any portfolio changes.

ELSE
- Generate an Investment Allocation discussion.
- Identify the asset class that is outside its bandwidth.
- Explain whether it is overweight or underweight.
- Suggest an appropriate Buy, Sell or Rebalance action.
- Base the recommendation ONLY on the provided portfolio data.

Discussion Point 2
------------------
Generate a Risk & Concerns discussion.

Use:
- Risk Indicators
- Theme Matches
- Market Sentiment
- Concentration Risk
- Security/Sector exposure

If a sector or security has negative sentiment,
mention it and explain why monitoring or reducing exposure may be appropriate.

If no major risk exists,
mention the primary risk indicator that should continue to be monitored.

Rules

- Return EXACTLY TWO discussion points.
- Make them client specific.
- Use ONLY the provided data.
- Never invent holdings or sectors.
- Professional Relationship Manager tone.
- Each discussion should be 2-3 sentences.
- No headings.
- No bullet points.

Return ONLY JSON.

{{
    "client_id":"client id",
    "portfolioDiscussion":[
        "discussion point 1",
        "discussion point 2"
    ]
}}
""".strip()

def generated_talking_points(client_ids: list[int] | None = None) -> dict:
    results = {}
    engine = init_db(DATABASE_URL)
    Session = get_session_factory(engine)
    openai_client = get_openai_client()

    with Session() as session:
        client_query = (
            session.query(ClientPersonalDetails, ClientMeetingSummary)
            .outerjoin(
                ClientMeetingSummary,
                ClientPersonalDetails.client_id == ClientMeetingSummary.client_id,
            )
        )
        if client_ids:
            client_query = client_query.filter(ClientPersonalDetails.client_id.in_(client_ids))
        clients = client_query.all()

        log.info("Starting talking-point generation for %s client(s)", len(clients))
        if not clients:
            log.warning("No clients found for talking-point generation")
            return results

        for client_details, meeting in clients:
            log.info(
                "Processing client %s: %s",
                client_details.id,
                _summarize_client(client_details, meeting),
            )
            conversation_result = populate_conversation_openers(
                session,
                [(client_details, meeting)],
                openai_client
            )

            portfolio_result = populate_portfolio_discussion(
                session,
                [(client_details, meeting)],
                openai_client
            )

            client_result = {
                "client_id": (
                        conversation_result.get("client_id")
                        or portfolio_result.get("client_id")
                ),
                "conversationOpeners": conversation_result.get(
                    "conversationOpeners",
                    []
                ),
                "portfolioDiscussion": portfolio_result.get(
                    "portfolioDiscussion",
                    []
                ),
            }

            row = get_or_create_client_talking_points(
                session,
                client_result
            )

            results[client_details.id] = row

        session.commit()
        log.info("Completed talking-point generation for %s client(s)", len(results))
        log.info("%s", "-" * 50)

    return results


def get_or_create_client_talking_points(session, client_result):
    client_id = client_result.get("client_id")
    openers = client_result.get("conversationOpeners", [])
    portfolio_discussion = client_result.get(
        "portfolioDiscussion",
        []
    )

    if not client_id:
        log.warning("Skipping DB write because no client_id was returned from the AI response")
        return None

    existing_row = session.query(ClientAITalkingPoints).filter_by(client_id=client_id).first()
    if existing_row:
        log.info(
            "Updating existing talking points for client_id=%s with %s opener(s)",
            client_id,
            len(openers),
        )
        existing_row.conversation_openers = openers
        existing_row.portfolio_discussion = portfolio_discussion
        session.flush()
        return existing_row

    row = ClientAITalkingPoints(client_id=client_id,
                                conversation_openers=openers,
                                portfolio_discussion=portfolio_discussion)
    session.add(row)
    session.flush()
    log.info("Created talking points for client_id=%s with %s opener(s)", client_id, len(openers))
    return row


def populate_conversation_openers(session, clients, openai_client):
    if not clients:
        return {"client_id": None, "conversationOpeners": []}

    client_lines = [
        (
            f"[{i}] {client_details.id} - {client_details.date_of_Birth} - "
            f"{client_details.marital_status} - {client_details.kids_details} - "
            f"{client_details.hobbies} - {client_details.other} - "
            f"{client_details.client_constraints} - "
            f"{meeting.main_discussion_points if meeting else 'No Meeting Summary'}"
        )
        for i, (client_details, meeting) in enumerate(clients)
    ]

    trends_block = "\n".join(client_lines)
    log.info("Preparing prompt with %s client entry/entries", len(client_lines))
    prompt = PROMPT_CONVERSATION_OPENERS.format(client_block=trends_block)
    log.debug("Prompt length: %s characters", len(prompt))

    result = openai_json(openai_client, prompt, SYSTEM_CONVERSATION_OPENERS)
    if isinstance(result, dict):
        opener_count = len(result.get("conversationOpeners", []))
        client_id = result.get("client_id")
        log.info("OpenAI returned %s opener(s) for client_id=%s", opener_count, client_id)
        if opener_count == 0:
            log.warning("No conversation openers were returned for client_id=%s", client_id)
        return result

    log.warning("Unexpected response shape from OpenAI: %s", type(result).__name__)
    return {"client_id": None, "conversationOpeners": result}

def populate_portfolio_discussion(session, clients, openai_client):

    if not clients:
        return {"client_id": None, "portfolioDiscussion": []}

    portfolio_sections = []

    for i, (client_details, meeting) in enumerate(clients):

        client = (
            session.query(Client)
            .filter(Client.id == client_details.client_id)
            .first()
        )

        portfolio_data = PortfolioApi.get_portfolio(client.id)

        performance_data = PortfolioApi.get_performance(
            client.id,
            client.rm_id
        )

        portfolio_text = f"""
        Portfolio Details:
        {json.dumps(portfolio_data, indent=2)}

        Performance Details:
        {json.dumps(performance_data, indent=2)}
        """


        risk = (
            session.query(ClientRiskOverview)
            .filter(ClientRiskOverview.client_id == client.id)
            .first()
        )

        risk_text = ""

        if risk:

            risk_text = f"""
    Concentration : {risk.concentration_pct}
    Largest Asset : {risk.concentration_asset}
    Sharpe Ratio : {risk.sharpe_ratio}
    Value At Risk : {risk.value_at_risk}
    Max Drawdown : {risk.max_drawdown}
    """

        theme_matches = (
            session.query(ClientThemeMatch)
            .filter(ClientThemeMatch.client_id == client.id)
            .all()
        )

        theme_text = []

        for theme in theme_matches:

            theme_text.append(
                f"""
    Theme : {theme.theme.name}
    Exposure : {theme.exposure_pct}
    Sentiment : {theme.sentiment}
    Confidence : {theme.confidence}
    """
            )

    portfolio_sections.append(
    f"""
    Client ID:{client.id}

    Risk Profile:
    {client.risk_profile}

    Portfolio Details:
    {portfolio_text}

    Risk Overview:
    {risk_text}

    Theme Matches:
    {''.join(theme_text)}
    """
        )

    portfolio_context = "\n".join(portfolio_sections)

    prompt = PROMPT_PORTFOLIO_DISCUSSION.format(
        portfolio_context = portfolio_context
    )

    result = openai_json(
        openai_client,
        prompt,
        SYSTEM_PORTFOLIO_DISCUSSION
    )

    if isinstance(result, dict):
        return {
            "client_id": result.get("client_id"),
            "portfolioDiscussion": result.get(
                "portfolioDiscussion",
                []
            ),
        }

    return {
        "client_id": None,
        "portfolioDiscussion": [],
    }

def get_openai_client() -> OpenAI:
    api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "sk-your-openai-key-here":
        raise RuntimeError(
            "OPENAI_API_KEY not set. "
            "Export it or update OPENAI_API_KEY in config/settings.py"
        )
    return OpenAI(api_key=api_key, http_client=httpx.Client(verify=False))


def openai_json(client: OpenAI, prompt: str, system: str) -> Any:
    """
    Call OpenAI and parse the response as JSON.
    Retries once on JSON decode failure.
    """
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                max_tokens=2048,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            parsed = json.loads(raw.strip())

            if isinstance(parsed, list):
                return parsed

            if isinstance(parsed, dict):

                if "conversationOpeners" in parsed:
                    return {
                        "client_id": parsed.get("client_id"),
                        "conversationOpeners": parsed.get(
                            "conversationOpeners",
                            []
                        ),
                    }

                if "portfolioDiscussion" in parsed:
                    return {
                        "client_id": parsed.get("client_id"),
                        "portfolioDiscussion": parsed.get(
                            "portfolioDiscussion",
                            []
                        ),
                    }

                return parsed

            return {}
        except json.JSONDecodeError as e:
            if attempt == 0:
                log.warning("JSON decode error, retrying: %s", e)
                time.sleep(1)
                continue
            log.exception("OpenAI returned invalid JSON after retry")
            raise
        except Exception as e:
            if "rate_limit" in str(e).lower():
                log.warning("Rate limit hit, sleeping 30s")
                time.sleep(30)
            log.exception("OpenAI request failed")
            raise




if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    generated_talking_points()