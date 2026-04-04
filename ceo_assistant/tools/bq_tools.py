import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET    = os.environ["BQ_DATASET"]


def _get_bq_client() -> bigquery.Client:
    """Create BigQuery client lazily to avoid import-time crashes in adk web."""
    return bigquery.Client(project=PROJECT_ID)


def list_tables() -> list[str]:
    """List all available tables in the dataset."""
    bq = _get_bq_client()
    tables = bq.list_tables(DATASET)
    return [t.table_id for t in tables]


def get_table_schema(table_name: str) -> str:
    """Get the schema (column names and types) for a given table."""
    bq = _get_bq_client()
    table = bq.get_table(f"{PROJECT_ID}.{DATASET}.{table_name}")
    schema_info = "\n".join(
        f"  {field.name}: {field.field_type}" for field in table.schema
    )
    return f"Table: {table_name}\nColumns:\n{schema_info}"


def run_query(sql: str) -> str:
    """Run a SQL query against BigQuery and return results as a string."""
    try:
        bq = _get_bq_client()
        results = bq.query(sql).result()
        rows = [dict(row) for row in results]
        if not rows:
            return "Query returned no results."
        return str(rows[:50])
    except Exception as e:
        return f"Query failed: {str(e)}"


def lookup_customer_email(name: str) -> str:
    """Look up a customer's email address from BigQuery by their name.

    Args:
        name: Full or partial customer name to search for.

    Returns:
        Customer name and email, or a not-found message.
    """
    try:
        bq  = _get_bq_client()
        sql = f"""
            SELECT DISTINCT `Customer Name`, `Customer Email`
            FROM `{PROJECT_ID}.{DATASET}.order_details`
            WHERE LOWER(`Customer Name`) LIKE LOWER('%{name}%')
            LIMIT 5
        """
        rows = [dict(row) for row in bq.query(sql).result()]
        if not rows:
            return f"No customer found matching '{name}'."
        lines = [f"- {r['Customer Name']}: {r['Customer Email']}" for r in rows]
        return "Found customers:\n" + "\n".join(lines)
    except Exception as e:
        return f"Email lookup failed: {str(e)}"
