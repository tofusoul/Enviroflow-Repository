"""
Helper functions for the SQL Query Explorer page.
"""

import duckdb
import streamlit as st
from typing import Dict, List, Any, Optional
from pathlib import Path
import re
from datetime import datetime

# Type alias for a query definition
QueryDefinition = Dict[str, Any]


@st.cache_resource
def get_motherduck_connection() -> duckdb.DuckDBPyConnection:
    """
    Establishes and caches a connection to MotherDuck.
    """
    token = st.secrets["motherduck"]["token"]
    try:
        con = duckdb.connect(f"md:?motherduck_token={token}", read_only=True)
        return con
    except Exception as e:
        st.error(f"Failed to connect to MotherDuck: {e}")
        return None


@st.cache_resource(ttl=3600)  # Cache for 1 hour
def get_db_schema(_conn: duckdb.DuckDBPyConnection) -> Dict[str, List[str]]:
    """
    Fetches the schema of all tables in the database and caches it.

    Args:
        _conn: An active connection to the MotherDuck database. The connection
               object itself is used as a key for caching.

    Returns:
        A dictionary where keys are table names and values are lists of column names.
    """
    schema = {}
    if not _conn:
        return schema

    try:
        tables_df = _conn.execute("SHOW TABLES;").fetchdf()
        for table_name in tables_df["name"]:
            columns_df = _conn.execute(f"PRAGMA table_info('{table_name}');").fetchdf()
            schema[table_name] = columns_df["name"].tolist()
    except Exception as e:
        st.error(f"Failed to fetch database schema: {e}")

    return schema


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_all_queries(
    _conn: duckdb.DuckDBPyConnection, user_email: str
) -> List[QueryDefinition]:
    """
    Fetches all available queries (pre-defined and custom), combining them and sorting by most recently used.

    Args:
        _conn: An active connection to the MotherDuck database.
        user_email: The email of the current user for personalization.

    Returns:
        A list of QueryDefinition dictionaries, sorted by `last_used_at` descending.
    """
    all_queries = []

    # 1. Load pre-defined queries from the filesystem
    predefined_queries = []
    query_dir = Path("enviroflow_app/db_queries")
    if query_dir.is_dir():
        for file_path in query_dir.glob("*.sql*"):
            with open(file_path, "r") as f:
                content = f.read()
            is_template = ".j2" in file_path.suffixes
            variables = (
                re.findall(r"\{\{\s*(\w+)\s*\}\}", content) if is_template else []
            )
            predefined_queries.append(
                {
                    "name": file_path.stem.replace(".sql", "")
                    .replace("_", " ")
                    .title(),
                    "id": file_path.name,
                    "sql": content,
                    "is_template": is_template,
                    "variables": variables,
                    "type": "Pre-defined",
                    "last_used_at": None,  # Will be populated from usage log
                }
            )

    # 2. Load custom queries from the database
    custom_queries = []
    if _conn:
        try:
            custom_queries_df = _conn.execute("SELECT * FROM custom_queries").fetchdf()
            for _, row in custom_queries_df.iterrows():
                custom_queries.append(
                    {
                        "name": row["name"],
                        "id": row["id"],
                        "sql": row["sql_template"],
                        "is_template": row["is_template"],
                        "variables": re.findall(
                            r"\{\{\s*(\w+)\s*\}\}", row["sql_template"]
                        )
                        if row["is_template"]
                        else [],
                        "type": "Custom",
                        "last_used_at": row["last_used_at"],
                        "created_by": row["created_by"],
                    }
                )
        except duckdb.Error as e:
            st.warning(f"Could not load custom queries: {e}")

    # 3. Load usage log for the current user to get timestamps for pre-defined queries
    if _conn:
        try:
            usage_log_df = _conn.execute(
                f"SELECT query_name, last_used_at FROM query_usage_log WHERE user_email = '{user_email}'"
            ).fetchdf()
            usage_map = {
                row["query_name"]: row["last_used_at"]
                for _, row in usage_log_df.iterrows()
            }
            for query in predefined_queries:
                if query["id"] in usage_map:
                    query["last_used_at"] = usage_map[query["id"]]
        except duckdb.Error as e:
            st.warning(f"Could not load query usage history: {e}")

    all_queries = predefined_queries + custom_queries

    # 4. Sort all queries by last_used_at
    # Use a very old date for queries that have never been used so they sort to the bottom.
    epoch_start = datetime(1970, 1, 1)
    all_queries.sort(key=lambda x: x.get("last_used_at") or epoch_start, reverse=True)

    return all_queries


def execute_query(
    _conn: duckdb.DuckDBPyConnection,
    query: str,
    template_vars: Optional[Dict[str, Any]] = None,
) -> Any:  # Returns Polars DF or error string
    """
    Executes a SQL query or a Jinja2 template against the database.

    Args:
        _conn: An active connection to the MotherDuck database.
        query: The SQL string or Jinja2 template.
        template_vars: A dictionary of variables to render the template with.

    Returns:
        A Polars DataFrame with the results, or a string with an error message.
    """
    if not _conn:
        return "No database connection available."

    final_query = query
    if template_vars:
        try:
            from jinja2 import Template

            template = Template(query)
            final_query = template.render(template_vars)
        except Exception as e:
            return f"Jinja2 template rendering error: {e}"

    try:
        result = _conn.execute(final_query).pl()
        return result
    except duckdb.Error as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def save_custom_query(
    _conn: duckdb.DuckDBPyConnection, name: str, sql: str, user_email: str
) -> tuple[bool, str]:
    """
    Validates and saves a new custom query to the database.

    Args:
        _conn: An active connection to the MotherDuck database.
        name: The name for the new query.
        sql: The SQL/Jinja2 string for the query.
        user_email: The email of the user saving the query.

    Returns:
        A tuple of (success: bool, message: str).
    """
    if not _conn:
        return False, "No database connection available."

    # Basic validation
    if not name.strip() or not sql.strip():
        return False, "Query name and SQL content cannot be empty."

    is_template = bool(re.search(r"\{\{\s*(\w+)\s*\}\}", sql))

    # --- Validation Step 1: Pre-flight check against schema ---
    db_schema = get_db_schema(_conn)
    try:
        import sqlparse

        parsed = sqlparse.parse(sql)
        stmt = parsed[0]
        for token in stmt.tokens:
            # This is a simplistic check; a more robust parser would build a proper dependency tree.
            # For now, we check for table names that might appear after FROM or JOIN.
            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in (
                "FROM",
                "JOIN",
            ):
                next_token = stmt.token_next(token)
                if next_token and next_token.ttype is sqlparse.tokens.Name:
                    if next_token.value not in db_schema:
                        return (
                            False,
                            f"Validation Error: Table '{next_token.value}' not found in database schema.",
                        )
    except ImportError:
        st.warning("`sqlparse` not installed. Skipping pre-flight schema check.")
    except Exception as e:
        st.warning(f"Could not perform pre-flight check: {e}")

    # --- Validation Step 2: Live execution check ---
    # For templates, we need mock data. This is a simplified approach.
    mock_vars = {}
    if is_template:
        variables = re.findall(r"\{\{\s*(\w+)\s*\}\}", sql)
        for var in variables:
            if "date" in var.lower():
                mock_vars[var] = datetime.now().date()
            elif "quote_no" in var.lower():
                mock_vars[var] = "QU-0000"  # A plausible dummy value
            else:
                mock_vars[var] = 1  # Default to a number

    validation_result = execute_query(_conn, sql, mock_vars)
    if isinstance(validation_result, str):
        return False, f"Query failed validation: {validation_result}"

    # --- Save to database ---
    try:
        import uuid

        query_id = uuid.uuid4()
        _conn.execute(
            "INSERT INTO custom_queries (id, name, sql_template, is_template, created_by, modified_by, modified_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [query_id, name, sql, is_template, user_email, user_email, datetime.now()],
        )
        # Basic validation passed, now try to save to the database
        try:
            query_id = uuid.uuid4()
            _conn.execute(
                """
                INSERT INTO custom_queries (id, name, sql_template, is_template, created_by, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, NOW(), NOW())
                """,
                [query_id, name, sql, is_template, user_email],
            )
            return True, f"Query saved successfully with ID: {query_id}"
        except duckdb.Error as e:
            return False, f"Failed to save query: {e}"
        except Exception as e:
            return False, f"An unexpected error occurred during save: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred during save: {e}"
