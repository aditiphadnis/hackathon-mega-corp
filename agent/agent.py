from __future__ import annotations

import asyncio
import uuid

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .sub_agents.bq_agent import bq_agent
from .sub_agents.calendar_agent import calendar_agent
from .sub_agents.notes_agent import notes_agent

# ── Orchestrator ──────────────────────────────────────────────────────────────

ceo_assistant = Agent(
    name="ceo_assistant",
    model="gemini-2.5-flash",
    description="CEO virtual assistant for Megacorp Universe.",
    instruction=(
        "You are the personal AI assistant to the CEO of Megacorp Universe. "
        "You have three specialist sub-agents available:\n\n"
        "1. **bq_agent** — answers questions about orders, sessions, revenue, "
        "and any other data stored in BigQuery. Use this for any analytical or "
        "data question.\n"
        "2. **calendar_agent** — schedules, lists, and manages meetings via "
        "Google Calendar. Use this whenever the CEO wants to book, view, or "
        "change calendar events.\n"
        "3. **notes_agent** — retrieves and analyses meeting notes stored in "
        "Notion. Use this when the CEO asks about past meeting summaries, "
        "action items, or decisions.\n\n"
        "Route each request to the most appropriate sub-agent. If a request "
        "spans multiple agents (e.g. 'schedule a follow-up based on last "
        "week's meeting notes'), coordinate them in sequence. Always respond "
        "in a concise, executive-friendly tone."
    ),
    sub_agents=[bq_agent, calendar_agent, notes_agent],
)

# Required by `adk web` and `adk api_server`
root_agent = ceo_assistant

# ── Runner (for direct programmatic use / testing) ────────────────────────────

session_service = InMemorySessionService()
runner = Runner(
    agent=ceo_assistant,
    app_name="megacorp_ceo",
    session_service=session_service,
)

APP_NAME   = "megacorp_ceo"
USER_ID    = str(uuid.uuid4())
SESSION_ID = str(uuid.uuid4())


async def init_session() -> None:
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )


async def chat(user_message: str) -> str:
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_message)],
    )
    response_text = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = "".join(
                p.text for p in event.content.parts if hasattr(p, "text")
            )
    return response_text


async def main() -> None:
    await init_session()
    print("Megacorp CEO Assistant ready\n")
    while True:
        user_input = input("CEO: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        reply = await chat(user_input)
        print(f"\nAssistant: {reply}\n")


if __name__ == "__main__":
    asyncio.run(main())