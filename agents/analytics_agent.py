# agents/analytics_agent.py
from google.adk import Agent
from google.adk.agents.mcp import McpToolset

# Connect to your MCP server
mcp_tools = McpToolset(url="http://localhost:8000")


analytics_agent = Agent(
    name="AnalyticsAgent",
    model="gemini-2.0-flash",
    instructions=(
        "You answer analytics questions using the MCP BigQuery tools. "
        "Prefer schema inspection before writing SQL. "
        "When writing SQL for `bq_run_query`, ONLY reference the allowed tables and use backticks "
        "for fully qualified names: `project.dataset.table`. "
        "Keep queries read-only and limit output rows. "
        "If the user asks for a chart, return data suitable for plotting (e.g., aggregated series)."
    ),
    tools=[
        mcp_tools.get_tool("list_bigquery_tables"),
        mcp_tools.get_tool("bq_get_table_schema"),
        mcp_tools.get_tool("bq_run_query"),
    ],
)

