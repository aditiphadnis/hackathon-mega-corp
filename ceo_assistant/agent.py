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
        "You have three specialist sub-agents:\n\n"
        "1. **bq_agent** — BigQuery data: orders, sessions, revenue, customers.\n"
        "2. **calendar_agent** — Google Calendar: schedule, view, edit meetings.\n"
        "3. **notes_agent** — Notion: retrieve and analyse meeting notes.\n\n"
        "Route each request to the best sub-agent. For multi-step requests "
        "(e.g. 'analyse Ross Geller then schedule a meeting'), coordinate "
        "sub-agents in sequence.\n\n"
        "CHART OUTPUT RULE — you MUST include a plotly JSON block whenever:\n"
        "  • The user explicitly asks for a chart or visualisation, OR\n"
        "  • The response contains a ranked or comparative list of items with numeric values "
        "(e.g. top customers, refunds by product, sales by region, failures by customer).\n\n"
        "When user asks about failed payment check the Interaction History field in the session_details table. If it says payment failed, then count that session.\n\n"
        "When the rule applies, respond with a text summary AND this EXACT block:\n\n"
        "```plotly\n"
        '{"chart_type": "bar", "title": "Top 10 Customers", "x": ["Name1", "Name2"], "y": [33, 32]}\n'
        "```\n\n"
        "chart_type must be one of: bar | line | pie\n"
        "Use 'labels' and 'values' instead of 'x' and 'y' for pie charts.\n"
        "Keep x labels short (≤20 chars). Round numeric values to 2 decimal places.\n"
        "Never say you cannot generate a chart.\n\n"
        "Always respond in a concise, executive-friendly tone."

    ),
    sub_agents=[bq_agent, calendar_agent, notes_agent],
)

root_agent = ceo_assistant

# ── Runner (for local testing) ────────────────────────────────────────────────

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
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID,
    )


async def chat(user_message: str) -> str:
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_message)],
    )
    response_text = ""
    async for event in runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=content,
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