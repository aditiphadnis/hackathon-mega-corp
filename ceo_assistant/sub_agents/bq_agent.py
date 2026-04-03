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
        f"Always use fully-qualified table names: `{PROJECT_ID}.{DATASET}.table_name`"
    ),
    tools=[list_tables, get_table_schema, run_query],
)