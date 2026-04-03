# agents/meeting_agent.py
from google.adk import Agent
from google.adk.agents.mcp import McpToolset

# Connect to your MCP server
mcp_tools = McpToolset(url="http://localhost:8000") 

meeting_agent = Agent(
    name="MeetingAgent",
    model="gemini-2.0-flash",
    instructions="You are an expert at scheduling. Use tool 'schedule_meeting' for all requests.",
    tools=[mcp_tools.get_tool("schedule_meeting"), mcp_tools.get_tool("get_customer_email")]
)