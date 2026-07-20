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

import httpx
from openai import OpenAI

from config.settings import DATABASE_URL, OPENAI_API_KEY, OPENAI_MODEL
from models import (
    Client,
    ClientAITalkingPoints,
    ClientMeetingSummary,
    ClientPersonalDetails,
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
            client_result = populate_conversation_openers([(client_details, meeting)], openai_client)
            if isinstance(client_result, dict):
                row = get_or_create_client_talking_points(session, client_result)
                results[client_details.id] = row

        session.commit()
        log.info("Completed talking-point generation for %s client(s)", len(results))
        log.info("%s", "-" * 50)

    return results


def get_or_create_client_talking_points(session, client_result):
    client_id = client_result.get("client_id")
    openers = client_result.get("conversationOpeners", [])

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
        session.flush()
        return existing_row

    row = ClientAITalkingPoints(client_id=client_id, conversation_openers=openers)
    session.add(row)
    session.flush()
    log.info("Created talking points for client_id=%s with %s opener(s)", client_id, len(openers))
    return row


def populate_conversation_openers(clients, openai_client):
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
                log.info("OpenAI returned a list payload with %s item(s)", len(parsed))
                return {"client_id": None, "conversationOpeners": parsed}
            if isinstance(parsed, dict):
                conversation_openers = parsed.get("conversationOpeners")
                if isinstance(conversation_openers, list):
                    log.info("OpenAI returned structured JSON with %s opener(s)", len(conversation_openers))
                    return {
                        "client_id": parsed.get("client_id"),
                        "conversationOpeners": conversation_openers,
                    }
                for v in parsed.values():
                    if isinstance(v, list):
                        log.info("OpenAI returned a wrapped list payload with %s item(s)", len(v))
                        return {
                            "client_id": parsed.get("client_id"),
                            "conversationOpeners": v,
                        }
                log.warning("OpenAI returned JSON without a conversationOpeners list. Keys: %s", list(parsed.keys()))
                return {"client_id": parsed.get("client_id"), "conversationOpeners": []}
            log.warning("OpenAI returned an unexpected payload type: %s", type(parsed).__name__)
            return {"client_id": None, "conversationOpeners": []}
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