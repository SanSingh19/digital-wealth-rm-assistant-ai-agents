import json
from pathlib import Path
from openai import OpenAI

from models import (
    Meeting,
    Client,
    ClientMeetingSummary,
    init_db,
    get_session_factory
)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import httpx

from config.settings import DATABASE_URL, OPENAI_API_KEY

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    http_client=httpx.Client(verify=False),
)


# ---------------- OUTPUT SCHEMA ----------------

class MeetingSummary(BaseModel):

    last_meeting_date: str = Field(
        description="Date of previous meeting"
    )

    main_discussion_points: list[str] = Field(
        description="Important discussion points"
    )

    client_questions: list[str] = Field(
        description="Questions asked by client"
    )


# ---------------- PARSER ----------------

PARSER = PydanticOutputParser(
    pydantic_object=MeetingSummary
)


# ---------------- PROMPT ----------------

PROMPT = ChatPromptTemplate.from_template("""
You are an experienced Wealth Management Assistant.

Below is the transcript of the previous client meeting.

Your task is to extract and summarize the key information from the meeting.

Instructions:
1. Identify the important discussion points.
2. Consolidate repeated, duplicate, or closely related discussion points into one clear key point.
3. Do not repeat the same information in multiple points.
4. Ignore greetings, small talk, filler words, and irrelevant conversation.
5. Extract important questions specifically asked by the client.
6. Consolidate duplicate or similar client questions.
7. Do not invent information that is not present in the transcript.
8. Keep the complete summary concise and within 100 words.

Meeting Transcript

{meeting_text}

{format_instructions}
""")


# ---------------- LLM ----------------

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
    api_key=OPENAI_API_KEY,
    http_client=httpx.Client(verify=False),
)

chain = PROMPT | llm | PARSER


# ---------------- LOAD AUDIO ----------------

def load_meeting(client_code):

    path = Path("meetings") / f"{client_code}.mp4"

    if not path.exists():
        return None

    with open(path, "rb") as audio_file:
        transcript = openai_client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file
        )

    return transcript.text


# ---------------- GENERATE SUMMARY ----------------

def generate_meeting_summary(client_code: str, meeting_date: str):

    meeting_text = load_meeting(client_code)

    if meeting_text is None:
        return {
            "last_meeting_date": "No previous meeting",
            "main_discussion_points": [],
            "client_questions": []
        }

    result = chain.invoke({
        "meeting_text": meeting_text,
        "format_instructions": PARSER.get_format_instructions()
    })

    return {
        "last_meeting_date": meeting_date,
        "main_discussion_points": result.main_discussion_points,
        "client_questions": result.client_questions
    }


def generate_client_meeting_summary(client_ids=None):

    engine = init_db(DATABASE_URL)
    Session = get_session_factory(engine)

    results = {}

    with Session() as session:

        client_query = session.query(Client)

        if client_ids:
            client_query = client_query.filter(Client.id.in_(client_ids))

        clients = client_query.all()

        for db_client in clients:

            print(f"\nGenerating summary for {db_client.client_code}")

            meeting = (
                session.query(Meeting)
                .filter(Meeting.client_id == db_client.id)
                .first()
            )

            if meeting and meeting.date and meeting.time:
                meeting_date = (
                    f"{meeting.date.strftime('%Y-%m-%d')} "
                    f"{meeting.time.strftime('%H:%M:%S')}"
                )
            elif meeting and meeting.date:
                meeting_date = meeting.date.strftime("%Y-%m-%d")
            else:
                meeting_date = "No meeting date"

            summary = generate_meeting_summary(
                db_client.client_code,
                meeting_date
            )

            existing_summary = (
                session.query(ClientMeetingSummary)
                .filter(ClientMeetingSummary.client_id == db_client.id)
                .first()
            )

            if existing_summary:

                existing_summary.rm_id = (
                    meeting.rm_id if meeting else db_client.rm_id
                )

                existing_summary.last_meeting_date = (
                    meeting.date if meeting else None
                )

                existing_summary.main_discussion_points = summary["main_discussion_points"]
                existing_summary.client_questions = summary["client_questions"]

                row = existing_summary

            else:

                row = ClientMeetingSummary(

                    rm_id=meeting.rm_id if meeting else db_client.rm_id,

                    client_id=db_client.id,

                    last_meeting_date=meeting.date if meeting else None,

                    main_discussion_points=summary["main_discussion_points"],
                    client_questions=summary["client_questions"]
                )

                session.add(row)

            results[db_client.id] = row

        session.commit()

    return results

if __name__ == "__main__":
    generate_client_meeting_summary()