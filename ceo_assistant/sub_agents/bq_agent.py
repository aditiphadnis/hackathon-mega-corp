from __future__ import annotations

import os

from dotenv import load_dotenv
from google.adk.agents import Agent

from ..tools.bq_tools import get_table_schema, list_tables, run_query

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET    = os.environ["BQ_DATASET"]

bq_agent = Agent(
    name="bq_agent",
    model="gemini-2.5-flash",
    description=(
        "Answers questions about orders, sessions, revenue, and any data in "
        "BigQuery. Always returns a clear summary of query results."
    ),
    instruction=(
    "You are a data analyst with direct access to BigQuery. "
    "When asked a data question:\n"
    "1. Call list_tables() to see available tables.\n"
    "2. Call get_table_schema() to understand columns.\n"
    "3. Write and run SQL with run_query().\n"
    "4. Return a concise summary — key numbers first, details below.\n"
    "If the user asks for a chart, return the data AND include a JSON block:\n"
    "If the user asks for top 10 customers by number of payment failures, check in the session_details table field named Interaction history and coount 'Payment Failures':\n"
    "If the user asks for Show me a bar chart of number sales by product, check in the oder_details table. All the orders are confirmed order. Calculate the count for each product and display top 10 \n"
    "CHART RULE — when the response contains a ranked or comparative list "
    "with numeric values, you MUST include this block using the EXACT fence "
    "marker ```plotly (never ```json):\n\n"
    "```plotly\n"
    '{"chart_type": "bar", "title": "...", "x": [...], "y": [...]}\n'
    "```\n\n"
    "chart_type: bar | line | pie. "
    "For pie charts use 'labels' and 'values' instead of 'x' and 'y'.\n"
    "Keep x labels ≤20 chars. Round values to 2 decimal places.\n"
    f"Always use fully-qualified table names: `{PROJECT_ID}.{DATASET}.table_name`"

    ),
    tools=[list_tables, get_table_schema, run_query],
)