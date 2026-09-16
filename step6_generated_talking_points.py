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
    ClientOutlook,
    ClientFundRecommendation,
    ClientAITalkingPoints,
    ClientMeetingSummary,
    ClientPersonalDetails,
    ClientRiskOverview,
    ClientThemeMatch,
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

def _summarize_client_product_introductions(
    outlook: Any,
    meeting_summary: Any,
    recommendation: Any
) -> str:

    recommendations = []

    if recommendation and recommendation.recommendations:
        try:
            recommendations = json.loads(
                recommendation.recommendations
            )
        except (json.JSONDecodeError, TypeError):
            recommendations = []

    return (
        f"client_id={outlook.client_id if outlook else recommendation.client_id if recommendation else 'Unknown'}, "
        f"client_question={_truncate(meeting_summary.client_questions) if meeting_summary else 'No Client Questions'}, "
        f"market_outlook={_truncate(outlook.headline_outlook) if outlook else 'No Market Outlook'}, "
        f"funds={json.dumps(recommendations, indent=2)}"
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

SYSTEM_ANTICIPATED_OBJECTIONS = """
You are an experienced Wealth Relationship Manager.

Generate anticipated client objections and professional responses.

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

SYSTEM_PRODUCT_INTRODUCTION = """
You are a Relationship Manager AI Assistant.

Your role is to suggest relevant financial products based on the client's questions, available market outlook, and fund information.

Respond ONLY with valid JSON – no preamble, no markdown fences.
""".strip()

PROMPT_PRODUCT_INTRODUCTION = """
Client Questions, Market Outlook, Funds and AI Recommendations:

{client_block}

Generate product introductions strictly from the AI Recommendations provided
in the input.

IMPORTANT:
The AI Recommendations are the ONLY source of allowed products/funds.
PRODUCT SELECTION RULES
-----------------------
1. Read every recommendation object in the AI Recommendations list.
2. A product/fund is eligible ONLY when:
   Action = "BUY"
3. Products/funds with:
   Action = "SELL"
   OR
   Action = "HOLD"
   are NOT eligible.
4. NEVER use a product/fund with Action = SELL.
5. NEVER use a product/fund with Action = HOLD.
6. NEVER use a product/fund only because it is mentioned in the Client Question.
7. NEVER use a product/fund only because it appears in the Market Outlook.
8. NEVER use a product/fund from your own knowledge.
9. NEVER invent a product/fund.
10. NEVER rename or modify an investment_name.
11. The product/fund name in the introduction MUST exactly match the
    investment_name from an AI Recommendation whose Action is BUY.

CLIENT QUESTION LOGIC
---------------------
If the Client Question mentions a specific product/fund:
- Find that product/fund in the AI Recommendations.
- Check its Action.
- If Action = BUY, use that exact investment_name for the first introduction.
- If Action = SELL, DO NOT use it.
- If Action = HOLD, DO NOT use it.
- If the mentioned product/fund does not exist in the AI Recommendations,
  DO NOT use it.
If the mentioned product/fund is SELL, HOLD, or does not exist:
- Ignore that product/fund completely.
- Select another product/fund ONLY from the AI Recommendations where
  Action = BUY.

BUY LIST IS A CLOSED LIST
-------------------------

Only the following products are allowed:
- Products whose Action is exactly BUY in the AI Recommendations.
Everything else is forbidden.
Do not select a product from:
- Client Question
- Market Outlook
- Sector
- Theme
- Rationale
- General financial knowledge
unless the exact investment_name also exists in the AI Recommendations
with Action = BUY.

INTRODUCTION RULES
------------------
If there are two or more BUY recommendations:
- Generate exactly 2 product introductions.
- Each introduction must use a different BUY recommendation.
- Both investment_name values must come directly from the BUY recommendations.
- Use the exact investment_name without changing it.
If there is exactly one BUY recommendation:
- Generate exactly 1 product introduction.
- Use that exact BUY investment_name.
- Do NOT invent a second product just to produce two introductions.
If there are no BUY recommendations:
- Return an empty product_introduction array.
- Do NOT invent or suggest any product.

STRICT SELL/HOLD RULE
---------------------

If a fund has Action = SELL:
NEVER say:
- explore the fund
- consider the fund
- invest in the fund
- add the fund
- opportunity in the fund
- discuss the fund as an investment
- recommend the fund

If a fund has Action = HOLD:
NEVER say:
- explore the fund
- consider the fund
- invest in the fund
- add the fund
- opportunity in the fund
- recommend the fund

A SELL or HOLD fund must not appear as a suggested product introduction.

FINAL CHECK BEFORE RETURNING
-----------------------------

Before returning each product introduction:
1. Identify the investment_name mentioned in the introduction.
2. Find the exact investment_name in the AI Recommendations.
3. Confirm that its Action is exactly BUY.
4. Confirm that the investment_name is unchanged.
5. Confirm that it is not SELL or HOLD.
6. Confirm that it has not already been used in another introduction.

If any check fails, do not use that product and select another BUY
recommendation.
Do not output the validation steps. Only output the final JSON.

STYLE
-----
- Professional.
- Client-friendly.
- Concise.
- Conversational.
- Relationship-focused.
- Use the recommendation rationale when relevant.
- Do not make guarantees.
- Do not provide personalized investment advice.
- Do not introduce any product outside the BUY recommendations.
Return ONLY valid JSON.

{{
  "client_id": "<use the current client's id from the client block>",
  "product_introduction": [
    "string"
  ]
}}
""".strip()

PROMPT_PORTFOLIO_DISCUSSION = """
Client Portfolio Information

{portfolio_context}

Generate EXACTLY TWO portfolio discussion points.

DISCUSSION POINT 1 – POSITIVE PORTFOLIO HIGHLIGHT
-------------------------------------------------

Always generate the first discussion point as a positive portfolio opening.
Use the provided Portfolio Details and Performance Details.
Discuss topics such as:
• YTD growth
• Portfolio performance
• Performance graph
• Strong asset allocation

This point should start the portfolio discussion in a positive and professional way.
Do NOT recommend any portfolio changes in this point.

--------------------------------------------------
DISCUSSION POINT 2 – DECISION LOGIC
--------------------------------------------------

Before writing the second discussion point, inspect EVERY asset in the Asset Allocation table.
For each asset class read ONLY the value of "InRange".
Count how many assets have:
InRange = NO
Decision:
IF count(NO) > 0
Generate ONLY an Asset Allocation discussion.

You MUST:
- identify every asset whose InRange = NO
- mention whether it is overweight or underweight by comparing Current Allocation with Recommended Bandwidth
- recommend Buy / Sell / Rebalance accordingly
- Do NOT generate anything apart from that

Risk discussion is STRICTLY FORBIDDEN.
-------------------------------------------------

IF count(NO) == 0
Generate ONLY a Risk & Concerns discussion.

Use ONLY
- Concentration Risk
- Largest Asset
- Theme Matches
- Theme Sentiment

Do NOT discuss allocation.

RULES:
• Return EXACTLY TWO discussion points.
• Point 1 MUST ALWAYS be a Positive Portfolio Highlight.
• Point 2 MUST follow the priority:
  1. Allocation Discussion (if any asset is outside range)
  Otherwise
  2. Risk & Concerns
• Never generate both Allocation and Risk discussions together.

• Previous Meeting Summary is additional context only.
• Use it ONLY when it contains important information directly relevant
  to the required portfolio discussion point.
• It MUST NOT change the Point 1 or Point 2 decision logic.
• It MUST NOT create an additional discussion topic.
• For Point 1, use only relevant meeting information that supports
  discussion of YTD growth, portfolio performance, performance graph,
  or asset allocation.
• For Point 2, use only relevant meeting information that supports
  the already selected Allocation Discussion or Risk & Concerns discussion.
• Ignore the Previous Meeting Summary if it is unrelated or not useful.

• Use ONLY the provided data.
• Never invent holdings, sectors or performance.
• Professional Wealth Relationship Manager tone.
• Keep responses concise and conversational.
• Maximum 2 concise sentences per discussion point.
• Use short professional wealth-management language.
• No headings and No bullet points.

Return ONLY JSON.

{{
    "client_id":"client id",
    "portfolioDiscussion":[
        "discussion point 1",
        "discussion point 2"
    ]
}}
""".strip()

PROMPT_ANTICIPATED_OBJECTIONS = """
Client Information

{fund_block}

Generate EXACTLY TWO anticipated objections.

Each objection should begin with:

"If the client..."

and immediately explain how the Relationship Manager should respond.

Use primarily:
- Client Constraints
- Risk Profile
- Recommended Fund Names
- Fund Sectors
- Recommendation Reason

Previous Meeting Discussion and Previous Client Questions are additional
context only.

Use them ONLY if they contain important information directly relevant to:
- concerns about investments
- risk concerns
- performance concerns
- questions about recommended funds
- client preferences or constraints related to investments

Ignore unrelated meeting information.
Do not invent information.

Rules

- Return EXACTly TWO objections.
- ALWAYS mention at least one recommended fund name in every objection whenever fund names are provided.
- If multiple funds are recommended, refer to them by name rather than saying "the recommendations" or "the funds."
- Never mention the absence of fund names if investment names exist in the input.
- Base objections only on the provided recommended funds.
- Mention sectors only if they are present in the input.
- Do not invent information.
- Make them client specific.
- Professional Relationship Manager tone.
- Keep each response concise.

Return ONLY JSON.

{{
    "client_id":"client id",
    "anticipatedObjections":[
        "string",
        "string"
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

        product_introduction_results = generated_product_introductions(client_ids)

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

            product_introduction_result = product_introduction_results.get(
                client_details.id,
                {"client_id": client_details.id, "product_introduction": []},
            )

            portfolio_result = populate_portfolio_discussion(
                session,
                [(client_details, meeting)],
                openai_client
            )

            objection_result = populate_anticipated_objections(
                session,
                [(client_details, meeting)],
                openai_client
            )

            client_result = {
                "client_id": (
                        conversation_result.get("client_id")
                        or portfolio_result.get("client_id")
                        or product_introduction_result.get("client_id")
                        or objection_result.get("client_id")
                        or client_details.id
                ),
                "conversationOpeners": conversation_result.get(
                    "conversationOpeners",
                    []
                ),
                "product_introduction": product_introduction_result.get(
                    "product_introduction",
                    []
                ),
                "portfolioDiscussion": portfolio_result.get(
                    "portfolioDiscussion",
                    []
                ),
                "anticipatedObjections": objection_result.get(
                        "anticipatedObjections",
                        []
                ),
                "conversation_openers_citation": conversation_result.get(
                    "citation",
                    {}
                ),
                "portfolio_discussion_citation": portfolio_result.get(
                    "citation",
                    {}
                ),
                "product_introduction_citation": product_introduction_result.get(
                    "citation",
                    {}
                ),
                "anticipated_objections_citation": objection_result.get(
                    "citation",
                    {}
                )
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

def generated_product_introductions(client_ids: list[int] | None = None) -> dict:
    results = {}
    engine = init_db(DATABASE_URL)
    Session = get_session_factory(engine)
    openai_client = get_openai_client()

    with Session() as session:
        client_query = (
            session.query(Client, ClientMeetingSummary, ClientOutlook, ClientFundRecommendation)
            .outerjoin(
                ClientMeetingSummary,
                Client.id == ClientMeetingSummary.client_id,
            )
            .outerjoin(
                ClientOutlook,
                Client.id == ClientOutlook.client_id,
            )
            .outerjoin(
                ClientFundRecommendation,
                Client.id == ClientFundRecommendation.client_id,
            )
        )
        if client_ids:
            client_query = client_query.filter(Client.id.in_(client_ids))
        clients = client_query.all()

        log.info("Starting Product Introduction generation for %s client(s)", len(clients))
        if not clients:
            log.warning("No clients found for Product Introduction generation")
            return results

        for client_details, meeting_summary, outlook, recommendation in clients:
            log.info(
                "Processing client %s: %s",
                client_details.id,
                _summarize_client_product_introductions(outlook, meeting_summary, recommendation),
            )
            client_result = populate_product_introductions([(outlook, meeting_summary, recommendation)], openai_client)
            if isinstance(client_result, dict):
                results[client_details.id] = client_result
            else:
                results[client_details.id] = {
                    "client_id": client_details.id,
                    "product_introduction": [],
                }

        log.info("Completed Product Introduction generation for %s client(s)", len(results))
        log.info("%s", "-" * 50)

    return results


def get_or_create_client_talking_points(session, client_result):
    client_id = client_result.get("client_id")
    openers = client_result.get("conversationOpeners", [])
    portfolio_discussion = client_result.get(
        "portfolioDiscussion",
        []
    )
    anticipated_objections = client_result.get(
        "anticipatedObjections",
        []
    )
    product_introduction = client_result.get("product_introduction", [])

    conversation_openers_citation = client_result.get(
        "conversation_openers_citation",
        {}
    )

    portfolio_discussion_citation = client_result.get(
        "portfolio_discussion_citation",
        {}
    )

    product_introduction_citation = client_result.get(
        "product_introduction_citation",
        {}
    )

    anticipated_objections_citation = client_result.get(
        "anticipated_objections_citation",
        {}
    )


    log.info(
        "openersFromAI=%s, introductionsFromAI=%s, portfolioDiscussionFromAI=%s",
        openers,
        product_introduction,
        portfolio_discussion,
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
        existing_row.product_introduction = product_introduction
        existing_row.anticipated_objections = anticipated_objections
        # Update citations
        existing_row.conversation_openers_citation = (
            conversation_openers_citation
        )
        existing_row.portfolio_discussion_citation = (
            portfolio_discussion_citation
        )
        existing_row.product_introduction_citation = (
            product_introduction_citation
        )
        existing_row.anticipated_objections_citation = (
            anticipated_objections_citation
        )
        session.flush()
        return existing_row

    row = ClientAITalkingPoints(
        client_id=client_id,
        conversation_openers=openers,
        portfolio_discussion=portfolio_discussion,
        product_introduction=product_introduction,
        anticipated_objections=anticipated_objections,
        # Citations
        conversation_openers_citation=conversation_openers_citation,
        portfolio_discussion_citation=portfolio_discussion_citation,
        product_introduction_citation=product_introduction_citation,
        anticipated_objections_citation=anticipated_objections_citation,

    )
    session.add(row)
    session.flush()
    log.info("Created talking points for client_id=%s with %s opener(s)", client_id, len(openers))
    return row


def populate_conversation_openers(session, clients, openai_client):
    if not clients:
        return {"client_id": None, "conversationOpeners": [], "citation": {}}

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

    # Store exactly the source/input data used to build the LLM input.
    citation = []

    for client_details, meeting in clients:
        citation.append({
            "date_of_Birth": client_details.date_of_Birth,
            "marital_status": client_details.marital_status,
            "kids_details": client_details.kids_details,
            "hobbies": client_details.hobbies,
            "other": client_details.other,
            "client_constraints": client_details.client_constraints,
            "main_discussion_points": (
                meeting.main_discussion_points
                if meeting
                else "No Meeting Summary"
            )
        })



    result = openai_json(openai_client, prompt, SYSTEM_CONVERSATION_OPENERS)
    if isinstance(result, dict):
        opener_count = len(result.get("conversationOpeners", []))
        client_id = result.get("client_id")
        log.info("OpenAI returned %s opener(s) for client_id=%s", opener_count, client_id)
        if opener_count == 0:
            log.warning("No conversation openers were returned for client_id=%s", client_id)
        return {
                    "client_id": client_id,
                    "conversationOpeners": result.get(
                        "conversationOpeners",
                        []
                    ),
                    "citation": citation
                }

    log.warning("Unexpected response shape from OpenAI: %s", type(result).__name__)
    return {"client_id": None, "conversationOpeners": result, "citation": citation}

def populate_product_introductions(clients, openai_client):
    if not clients:
        return {"client_id": None, "product_introduction": [],"citation": {}}

    client_lines = [
        _summarize_client_product_introductions(
            outlook,
            meeting_summary,
            recommendation
        )
        for outlook, meeting_summary, recommendation in clients
    ]

    client_block = "\n".join(
        f"[{i}] {line}" for i, line in enumerate(client_lines)
    )

    log.info(
        "Preparing product introduction prompt with %s client entry/entries",
        len(client_lines)
    )

    prompt = PROMPT_PRODUCT_INTRODUCTION.format(
        client_block=client_block
    )

    log.debug("Prompt length: %s characters", len(prompt))

    # Store the same input data used by _summarize_client_product_introductions().
    # Store the source/input data used by the LLM prompt.
    citation = []

    for outlook, meeting_summary, recommendation in clients:

        recommended_funds_citation = []

        if recommendation and recommendation.recommendations:
            try:
                funds = json.loads(recommendation.recommendations)

                for fund in funds:
                    recommended_funds_citation.append({
                        "investment_name": fund.get("investment_name"),
                        "sector": fund.get("sector"),
                        "action": fund.get("action"),
                        "priority": fund.get("priority"),
                        "rationale": fund.get("rationale")
                    })

            except (json.JSONDecodeError, TypeError):
                recommended_funds_citation = []

        citation.append({
            "client_question": (
                _truncate(meeting_summary.client_questions)
                if meeting_summary
                else "No Client Questions"
            ),
            "market_outlook": (
                outlook.headline_outlook
                if outlook
                else "No Market Outlook"
            ),
            "funds": recommended_funds_citation
        })



    result = openai_json(
        openai_client,
        prompt,
        SYSTEM_PRODUCT_INTRODUCTION
    )

    if isinstance(result, dict):
        introduction_count = len(
            result.get("product_introduction", [])
        )
        client_id = result.get("client_id")

        log.info(
            "OpenAI returned %s product introduction(s) for client_id=%s",
            introduction_count,
            client_id
        )

        if introduction_count == 0:
            log.warning(
                "No product introductions were returned for client_id=%s",
                client_id
            )

        return {
                   "client_id": client_id,
                   "product_introduction": result.get(
                       "product_introduction",
                       []
                   ),
                   "citation": citation
               }

    log.warning(
        "Unexpected response shape from OpenAI: %s",
        type(result).__name__
    )

    return {
        "client_id": None,
        "product_introduction": result,
        "citation": citation
    }

def populate_portfolio_discussion(session, clients, openai_client):

    if not clients:
        return {"client_id": None, "portfolioDiscussion": [],"citation": {}}

    portfolio_sections = []
    citation = []


    for i, (client_details, meeting) in enumerate(clients):

        meeting_text = (
            meeting.main_discussion_points
            if meeting and meeting.main_discussion_points
            else "No relevant previous meeting discussion available"
        )

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

    Previous Meeting Summary:
    {meeting_text}

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

         # Citation contains the source/input data used for the LLM prompt.
        citation.append({
            "previous_meeting_summary": meeting_text,
            "risk_profile": client.risk_profile,

            "portfolio_details": {
                "portfolioMarketValue": portfolio_data.get("portfolioMarketValue"),
                "assetAllocation": portfolio_data.get("assetAllocation", []),
            },

            "performance_details": {
                "period": performance_data.get("period"),
                "ytdReturn": performance_data.get("ytdReturn"),
            },

            "risk_overview": {
                "concentration": (
                    risk.concentration_pct
                    if risk else None
                ),
                "largest_asset": (
                    risk.concentration_asset
                    if risk else None
                ),
                "sharpe_ratio": (
                    risk.sharpe_ratio
                    if risk else None
                ),
                "value_at_risk": (
                    risk.value_at_risk
                    if risk else None
                ),
                "max_drawdown": (
                    risk.max_drawdown
                    if risk else None
                ),
            },

            "theme_matches": [
                {
                    "theme": theme.theme.name,
                    "exposure": theme.exposure_pct,
                    "sentiment": theme.sentiment,
                    "confidence": theme.confidence,
                }
                for theme in theme_matches
            ],
        })

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
            "citation": citation
        }

    return {
        "client_id": None,
        "portfolioDiscussion": [],
        "citation": citation
    }

def populate_anticipated_objections(session, clients, openai_client):

    if not clients:
        return {
            "client_id": None,
            "anticipatedObjections": [],
            "citation": {}
        }

    fund_lines = []
    citation = []

    for client_details, meeting in clients:

        meeting_discussion = (
            meeting.main_discussion_points
            if meeting and meeting.main_discussion_points
            else "No relevant previous meeting discussion"
        )

        client_questions = (
            meeting.client_questions
            if meeting and meeting.client_questions
            else "No previous client questions"
        )

        client = (
            session.query(Client)
            .filter(Client.id == client_details.client_id)
            .first()
        )

        recommendation = (
            session.query(ClientFundRecommendation)
            .filter(ClientFundRecommendation.client_id == client.id)
            .first()
        )

        fund_text = []
        recommended_funds_citation = []

        if recommendation and recommendation.recommendations:

            funds = json.loads(recommendation.recommendations)

            for fund in funds:

                fund_text.append(
                    f"""
                    Fund Name : {fund.get("investment_name")}
                    Sector : {fund.get("sector")}
                    Action : {fund.get("action")}
                    Priority : {fund.get("priority")}
                    Reason : {fund.get("rationale")}
                    """
                )

                recommended_funds_citation.append({
                    "investment_name": fund.get("investment_name"),
                    "sector": fund.get("sector"),
                    "action": fund.get("action"),
                    "priority": fund.get("priority"),
                    "rationale": fund.get("rationale")
                })

        fund_lines.append(
            f"""
Client ID:
{client.id}

Risk Profile:
{client.risk_profile}

Client Constraints:
{client_details.client_constraints}

Previous Meeting Discussion:
{meeting_discussion}

Previous Client Questions:
{client_questions}

Recommended Funds:
{''.join(fund_text)}
"""
        )

        # Citation contains the source/input data used for the LLM prompt.
        citation.append({
            "risk_profile": client.risk_profile,
            "client_constraints": client_details.client_constraints,
            "previous_meeting_discussion": meeting_discussion,
            "previous_client_questions": client_questions,
            "recommended_funds": recommended_funds_citation
        })

    fund_block = "\n".join(fund_lines)

    prompt = PROMPT_ANTICIPATED_OBJECTIONS.format(
        fund_block=fund_block
    )

    result = openai_json(
        openai_client,
        prompt,
        SYSTEM_ANTICIPATED_OBJECTIONS
    )

    if isinstance(result, dict):

        return {
            "client_id": result.get("client_id"),
            "anticipatedObjections": result.get(
                "anticipatedObjections",
                []
            ),
            "citation": citation
        }

    return {
        "client_id": None,
        "anticipatedObjections": [],
        "citation": citation
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
                if "anticipatedObjections" in parsed:
                    return {
                        "client_id": parsed.get("client_id"),
                        "anticipatedObjections": parsed.get(
                            "anticipatedObjections",
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