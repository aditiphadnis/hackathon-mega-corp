from __future__ import annotations

from google.adk.agents import Agent

from ..tools.vector_notes_tools import (
    list_all_notes,
    search_meeting_notes,
    upload_meeting_note,
)

notes_agent = Agent(
    name="notes_agent",
    model="gemini-2.5-flash",
    description=(
        "Semantically searches and retrieves meeting notes using Vertex AI "
        "Vector Search. Use for questions about past meetings, action items, "
        "decisions, or summaries."
    ),
    instruction=(
        "You manage the CEO's meeting notes using semantic vector search.\n\n"
        "Capabilities:\n"
        "- list_all_notes(): Show all indexed notes.\n"
        "- search_meeting_notes(query): Find the most relevant notes using "
        "semantic similarity — use natural language queries like "
        "'payment failures' or 'Krypton Core strategy'.\n"
        "- upload_meeting_note(title, date, attendees, content): Index a new note.\n\n"
        "Workflow:\n"
        "1. For search requests, call search_meeting_notes() with a descriptive query.\n"
        "2. Summarise results: key decisions, action items with owners/dates.\n"
        "3. Always highlight the similarity score to show relevance.\n"
        "Be concise and executive-friendly."
    ),
    tools=[list_all_notes, search_meeting_notes, upload_meeting_note],
)