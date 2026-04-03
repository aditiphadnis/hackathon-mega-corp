import os
from google.adk.agents import Agent
from .tools.bq_tools import list_tables, get_table_schema, run_query
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET    = os.environ["BQ_DATASET"]

bq_agent = Agent(
    name="bigquery_assistant",
    model="gemini-2.5-flash",
    description="An agent that answers questions by querying BigQuery.",
    instruction=(
        "You are a data analyst with access to BigQuery. "
        "When the user asks a question about data:\n"
        "1. First call list_tables() to see available tables\n"
        "2. Call get_table_schema() to understand the columns\n"
        "3. Write and run a SQL query using run_query()\n"
        "4. Summarise the results clearly for the user\n"
        "Always use fully qualified table names in SQL: "
        f"`{PROJECT_ID}.{DATASET}.table_name`"
    ),
    tools=[list_tables, get_table_schema, run_query],
)