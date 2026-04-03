# mcp_server.py
import asyncio
import os
import re
from typing import Any, Dict, List, Set

from mcp.server.fastmcp import FastMCP

try:
    # Optional dependency (repo currently doesn't include it).
    import firestore_client  # type: ignore
except Exception:  # pragma: no cover
    firestore_client = None

try:
    from google.cloud import bigquery  # type: ignore
except Exception:  # pragma: no cover
    bigquery = None


mcp = FastMCP("Mega-Corp")


# Hard-limit access to your two tables (prevents arbitrary SQL access).
ALLOWED_BIGQUERY_TABLES: Set[str] = {
    "ai-agent-use-cases-485910.hackathon_mega_corp_universe.order_details",
    "ai-agent-use-cases-485910.hackathon_mega_corp_universe.session_details",
}


def _require_firestore() -> None:
    if firestore_client is None:
        raise RuntimeError(
            "Firestore tools are not configured in this repo (missing `firestore_client`). "
            "If you don't need Firestore, ignore these tools; for BigQuery use the `bq_*` tools."
        )


def _require_bigquery() -> None:
    if bigquery is None:
        raise RuntimeError(
            "BigQuery client library is not available. Install `google-cloud-bigquery` "
            "and ensure credentials are set (ADC or service account)."
        )


def _validate_sql(sql: str) -> None:
    sql_no_semicolon = ";" not in sql
    if not sql_no_semicolon:
        raise ValueError("SQL must not contain semicolons.")

    forbidden = [
        r"\bDROP\b",
        r"\bDELETE\b",
        r"\bUPDATE\b",
        r"\bINSERT\b",
        r"\bALTER\b",
        r"\bCREATE\b",
        r"\bTRUNCATE\b",
        r"\bEXEC\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
    ]
    for pat in forbidden:
        if re.search(pat, sql, flags=re.IGNORECASE):
            raise ValueError(f"Forbidden SQL keyword detected: `{pat}`")

    table_refs = set(re.findall(r"`([^`]+)`", sql))
    if not table_refs:
        raise ValueError(
            "SQL must reference allowed tables using backticks, e.g. "
            "`project.dataset.table`."
        )

    unknown = table_refs - ALLOWED_BIGQUERY_TABLES
    if unknown:
        raise ValueError(f"SQL references unknown tables: {sorted(unknown)}")

    # Also ensure we don't reference other tables in unquoted form (best-effort).
    # If your agent writes without backticks, it will fail anyway above.


@mcp.tool()
async def list_bigquery_tables() -> List[str]:
    """List the BigQuery tables this MCP server is allowed to access."""
    return sorted(ALLOWED_BIGQUERY_TABLES)


@mcp.tool()
async def bq_get_table_schema(table_fqn: str) -> Dict[str, Any]:
    """Return a lightweight schema for an allowed table."""
    _require_bigquery()

    table_fqn = table_fqn.strip()
    if table_fqn not in ALLOWED_BIGQUERY_TABLES:
        raise ValueError(f"Table not allowed: {table_fqn}")

    parts = table_fqn.split(".")
    if len(parts) != 3:
        raise ValueError("`table_fqn` must be in the form `project.dataset.table`.")
    project, dataset, table = parts

    client = bigquery.Client()
    tbl = client.get_table(f"{project}.{dataset}.{table}")
    return {
        "table": table_fqn,
        "num_rows_estimate": int(getattr(tbl, "num_rows", 0) or 0),
        "schema": [
            {"name": f.name, "type": f.field_type, "mode": f.mode}
            for f in (tbl.schema or [])
        ],
    }


@mcp.tool()
async def bq_run_query(sql: str, max_rows: int = 50) -> List[Dict[str, Any]]:
    """
    Run a read-only query against the allowed tables.

    Safety rules:
    - Only tables in `ALLOWED_BIGQUERY_TABLES`
    - Tables must be referenced with backticks: `project.dataset.table`
    - No semicolons, and common write/DDL keywords are rejected
    """
    _require_bigquery()
    _validate_sql(sql)

    if max_rows < 1 or max_rows > 500:
        raise ValueError("`max_rows` must be between 1 and 500.")

    client = bigquery.Client()

    # BigQuery python client is sync; run it in a thread to avoid blocking.
    def _run() -> List[Dict[str, Any]]:
        job = client.query(sql)
        res = job.result(max_results=max_rows)
        return [dict(row) for row in res]

    return await asyncio.to_thread(_run)


# --------------------
# (Optional) Firestore tools used by MeetingAgent
# --------------------


@mcp.tool()
async def query_orders(customer_id: str) -> Any:
    """Fetch order history from Firestore (optional; not used for BigQuery integration)."""
    _require_firestore()
    return firestore_client.get_orders(customer_id)


@mcp.tool()
async def schedule_meeting(title: str, time: str, attendees: list) -> Any:
    """Add an event to the calendar and store in Firestore (optional)."""
    _require_firestore()
    return firestore_client.save_meeting(title, time, attendees)


@mcp.tool()
async def get_customer_email(customer_id: str) -> str:
    """Look up a customer's email address from Firestore (optional)."""
    _require_firestore()
    return firestore_client.get_customer_email(customer_id)


# --------------------
# Misc tools (safe stubs)
# --------------------


@mcp.tool()
async def send_email(recipient: str, subject: str, body: str) -> Dict[str, str]:
    """Sends a formatted email to a customer or colleague (stub)."""
    # If you want real email delivery, wire this up to an SMTP/Gmail integration.
    print(f"Sending email to {recipient}...")
    return {"status": "sent", "recipient": recipient, "subject": subject}


@mcp.tool()
async def search_emails(query: str) -> List[Dict[str, str]]:
    """Search for previous email threads to get context (stub)."""
    return [{"from": "boss@megacorp.com", "content": f"Search result for: {query}"}]