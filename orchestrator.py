# orchestrator.py
from google.adk import Agent
from google.adk.agents import AgentTool
from agents.meeting_agent import meeting_agent
from agents.analytics_agent import analytics_agent

# Wrap sub-agents as tools for the Orchestrator
tools = [
    AgentTool(agent=meeting_agent),
    AgentTool(agent=analytics_agent)
]

orchestrator = Agent(
    name="Orchestrator",
    model="gemini-2.0-flash",
    instructions="Review user query. Delegate to AnalyticsAgent for charts/orders or MeetingAgent for schedules.",
    tools=tools
)