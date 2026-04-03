from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

# Notion MCP — the same URL you have connected in Claude
NOTION_MCP_URL = "https://mcp.notion.com/mcp"

notes_agent = Agent(
    name="notes_agent",
    model="gemini-2.5-flash",
    description=(
        "Retrieves and analyses meeting notes from Notion. Use for questions "
        "about past meetings, action items, decisions, or summaries."
    ),
    instruction=(
        "You have access to the CEO's Notion workspace which contains meeting "
        "notes. When asked about a meeting or notes:\n"
        "1. Search for the relevant page(s) by title, date, or keywords.\n"
        "2. Retrieve the full content of matching pages.\n"
        "3. Return a structured summary: key decisions, action items, and "
        "open questions. Format action items as a bullet list with owner and "
        "due date where available.\n"
        "If multiple pages match, summarise all of them and highlight "
        "differences or patterns."
    ),
    tools=[
        MCPToolset(
            connection_params=SseServerParams(url=NOTION_MCP_URL),
        )
    ],
)