from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

# Google Calendar MCP — the same URL you have connected in Claude
GCAL_MCP_URL = "https://gcal.mcp.claude.com/mcp"

calendar_agent = Agent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description=(
        "Schedules, lists, and manages meetings on Google Calendar. "
        "Use for any request involving booking, viewing, or editing events."
    ),
    instruction=(
        "You manage the CEO's Google Calendar. You can:\n"
        "- List upcoming events (always show date, time, and attendees).\n"
        "- Create new events (confirm title, date/time, attendees, and "
        "duration with the user before creating).\n"
        "- Update or cancel existing events.\n"
        "Always confirm actions before making changes. Use ISO 8601 for "
        "dates internally, but display them in a human-friendly format."
    ),
    tools=[
        MCPToolset(
            connection_params=SseServerParams(url=GCAL_MCP_URL),
        )
    ],
)