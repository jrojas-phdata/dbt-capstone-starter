#!/usr/bin/env python3
import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any

import snowflake.connector
import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent


def _find_profiles_path() -> Path:
    env_dir = os.environ.get("DBT_PROFILES_DIR")
    if env_dir:
        candidate = Path(env_dir) / "profiles.yml"
        if candidate.exists():
            return candidate
    global_candidate = Path.home() / ".dbt" / "profiles.yml"
    if global_candidate.exists():
        return global_candidate
    local_candidate = PROJECT_ROOT / "profiles.yml"
    if local_candidate.exists():
        return local_candidate
    raise FileNotFoundError(
        "profiles.yml not found. Set DBT_PROFILES_DIR or place profiles.yml in ~/.dbt/ or project root."
    )


def _load_creds() -> dict:
    profiles_path = _find_profiles_path()
    with open(profiles_path) as f:
        profiles = yaml.safe_load(f)
    return profiles["default"]["outputs"]["dev"]


CREDS = _load_creds()

# ---------------------------------------------------------------------------
# Snowflake connection (module-level singleton with lazy reconnect)
# ---------------------------------------------------------------------------

_conn: snowflake.connector.SnowflakeConnection | None = None


def _normalize_account(account: str) -> str:
    # Newer connector versions reject the old "accountlocator.region" format.
    # Strip any trailing ".region" suffix so only the locator remains.
    if "." in account:
        return account.split(".")[0]
    return account


def _connect() -> snowflake.connector.SnowflakeConnection:
    authenticator = CREDS.get("authenticator", "snowflake")
    kwargs: dict[str, Any] = dict(
        account=_normalize_account(CREDS["account"]),
        user=CREDS["user"],
        role=CREDS.get("role"),
        warehouse=CREDS.get("warehouse"),
        database=CREDS.get("database"),
        authenticator=authenticator,
    )
    if authenticator == "snowflake":
        kwargs["password"] = CREDS["password"]
    return snowflake.connector.connect(**kwargs)


def get_connection() -> snowflake.connector.SnowflakeConnection:
    global _conn
    try:
        if _conn is None or _conn.is_closed():
            _conn = _connect()
            return _conn
        cur = _conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return _conn
    except Exception:
        _conn = _connect()
        return _conn


# ---------------------------------------------------------------------------
# Read-only SQL guard
# ---------------------------------------------------------------------------

_WRITE_TOKENS = {
    "INSERT", "UPDATE", "DELETE", "MERGE", "CREATE", "DROP", "ALTER",
    "TRUNCATE", "GRANT", "REVOKE", "EXECUTE", "CALL", "BEGIN", "COMMIT",
    "ROLLBACK",
}

_COMMENT_RE = re.compile(r"(--[^\n]*|/\*.*?\*/)", re.DOTALL)


def _is_read_only(sql: str) -> tuple[bool, str]:
    stripped = _COMMENT_RE.sub("", sql).strip()
    first_token = stripped.split()[0].upper() if stripped.split() else ""
    if first_token in _WRITE_TOKENS:
        return False, f"Statement type '{first_token}' is not allowed. Only SELECT and WITH queries are permitted."
    parts = [p.strip() for p in stripped.split(";") if p.strip()]
    if len(parts) > 1:
        return False, "Multiple statements separated by ';' are not allowed."
    return True, ""


# ---------------------------------------------------------------------------
# dbt schema resolution
# ---------------------------------------------------------------------------

_LAYER_SCHEMA_MAP = {
    "staging": "stage",
    "intermediate": "intermediate",
    "marts": "data_mart",
}


def _resolve_dbt_schema(model_name: str) -> tuple[str, str] | tuple[None, str]:
    """Return (resolved_schema, error_message). resolved_schema is None on failure."""
    for root, dirs, files in os.walk(PROJECT_ROOT / "models"):
        if f"{model_name}.sql" in files:
            rel = Path(root).relative_to(PROJECT_ROOT / "models").parts
            for layer_key, custom_schema in _LAYER_SCHEMA_MAP.items():
                if layer_key in rel:
                    target_schema = CREDS["schema"].strip().upper()
                    resolved = f"{target_schema}_{custom_schema.upper()}"
                    return resolved, ""
            return None, f"Model '{model_name}' found but its layer directory could not be mapped to a schema."
    return None, (
        f"Model file '{model_name}.sql' not found under models/. "
        "Ensure the model exists and has been materialized in Snowflake."
    )


# ---------------------------------------------------------------------------
# Result serialization
# ---------------------------------------------------------------------------

def _rows_to_dicts(cursor) -> list[dict]:
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchmany(500)
    return [{col: _serialize(val) for col, val in zip(columns, row)} for row in rows]


def _serialize(val: Any) -> Any:
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return val


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

app = Server("snowflake-dbt")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="execute_query",
            description="Run a read-only SELECT query against Snowflake. Returns up to 500 rows.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "A SELECT or WITH query to execute."},
                },
                "required": ["sql"],
            },
        ),
        types.Tool(
            name="list_schemas",
            description="List all schemas in a Snowflake database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string", "description": "Database name. Defaults to the dbt dev database."},
                },
            },
        ),
        types.Tool(
            name="list_tables",
            description="List all tables and views in a Snowflake schema.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name."},
                    "database": {"type": "string", "description": "Database name. Defaults to the dbt dev database."},
                },
                "required": ["schema"],
            },
        ),
        types.Tool(
            name="describe_table",
            description="Return column names, types, and nullability for a Snowflake table or view.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Table or view name."},
                    "schema": {"type": "string", "description": "Schema name."},
                    "database": {"type": "string", "description": "Database name. Defaults to the dbt dev database."},
                },
                "required": ["table_name", "schema"],
            },
        ),
        types.Tool(
            name="preview_dbt_model",
            description=(
                "Preview rows from a materialized dbt model by model name. "
                "Automatically resolves the Snowflake schema using the project's generate_schema_name convention."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "description": "dbt model name without .sql extension (e.g. 'dim_customers')."},
                    "limit": {"type": "integer", "description": "Number of rows to return. Defaults to 10.", "default": 10},
                },
                "required": ["model_name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        result = _dispatch(name, arguments)
        import json
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]


def _dispatch(name: str, args: dict) -> Any:
    db = args.get("database") or CREDS.get("database", "sandbox")

    if name == "execute_query":
        sql = args["sql"]
        ok, reason = _is_read_only(sql)
        if not ok:
            return {"error": reason}
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        return _rows_to_dicts(cur)

    elif name == "list_schemas":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"SHOW SCHEMAS IN DATABASE {db}")
        rows = cur.fetchall()
        # column 1 (index 1) is the schema name in SHOW SCHEMAS output
        return [row[1] for row in rows]

    elif name == "list_tables":
        schema = args["schema"]
        conn = get_connection()
        cur = conn.cursor()
        results = []
        for kind in ("TABLES", "VIEWS"):
            cur.execute(f"SHOW {kind} IN SCHEMA {db}.{schema}")
            for row in cur.fetchall():
                results.append({"name": row[1], "kind": kind.rstrip("S"), "created_on": str(row[0])})
        return results

    elif name == "describe_table":
        table = args["table_name"]
        schema = args["schema"]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"DESCRIBE TABLE {db}.{schema}.{table}")
        rows = cur.fetchall()
        cols = [col[0] for col in cur.description]
        # Return the most useful fields: name, type, null?, default
        keep = {"name", "type", "null?", "default"}
        return [
            {col: _serialize(val) for col, val in zip(cols, row) if col.lower() in keep}
            for row in rows
        ]

    elif name == "preview_dbt_model":
        model = args["model_name"]
        limit = int(args.get("limit") or 10)
        resolved_schema, err = _resolve_dbt_schema(model)
        if resolved_schema is None:
            return {"error": err}
        sql = f"SELECT * FROM {db}.{resolved_schema}.{model.upper()} LIMIT {limit}"
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        return {"schema": resolved_schema, "sql": sql, "rows": _rows_to_dicts(cur)}

    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
