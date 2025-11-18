import pytest
import duckdb
from pathlib import Path
import os

# Mock streamlit before importing helpers
from unittest.mock import MagicMock
import sys

sys.modules["streamlit"] = MagicMock()

from enviroflow_app.helpers.query_helpers import save_custom_query, get_all_queries


@pytest.fixture
def db_connection():
    """Fixture to create an in-memory DuckDB for integration tests."""
    conn = duckdb.connect(":memory:")
    # Create necessary tables
    conn.execute("""
        CREATE TABLE custom_queries (
            id UUID PRIMARY KEY, name VARCHAR NOT NULL UNIQUE, sql_template VARCHAR NOT NULL,
            created_by VARCHAR, created_at TIMESTAMP, modified_by VARCHAR,
            modified_at TIMESTAMP, is_template BOOLEAN NOT NULL, last_used_at TIMESTAMP
        );
    """)
    conn.execute("""
        CREATE TABLE query_usage_log (
            query_name VARCHAR, user_email VARCHAR, last_used_at TIMESTAMP NOT NULL,
            PRIMARY KEY (query_name, user_email)
        );
    """)
    conn.execute("CREATE TABLE real_table (id INTEGER);")
    yield conn
    conn.close()


def test_save_and_get_custom_query(db_connection):
    """Tests saving a custom query and then retrieving it."""
    user = "test@example.com"
    query_name = "My Test Query"
    query_sql = "SELECT * FROM real_table"

    # Save the query
    success, msg = save_custom_query(db_connection, query_name, query_sql, user)
    assert success, f"Save failed: {msg}"

    # Retrieve all queries
    # Create a dummy predefined query file for get_all_queries to find
    dummy_dir = Path("enviroflow_app/db_queries")
    dummy_dir.mkdir(exist_ok=True)
    dummy_file = dummy_dir / "dummy.sql"
    with open(dummy_file, "w") as f:
        f.write("SELECT 1")

    # Access the wrapped function to bypass the @st.cache_data decorator
    all_queries = get_all_queries.__wrapped__(db_connection, user)

    os.remove(dummy_file)  # Clean up

    # Check if the custom query is in the list
    custom_query_found = False
    for q in all_queries:
        if q["name"] == query_name and q["type"] == "Custom":
            custom_query_found = True
            assert q["sql"] == query_sql
            assert q["created_by"] == user
            break

    assert custom_query_found, "Saved custom query was not found."


def test_log_and_retrieve_usage(db_connection):
    """Tests that usage is logged and affects sorting."""
    user = "test@example.com"

    # Create dummy predefined query files
    dummy_dir = Path("enviroflow_app/db_queries")
    dummy_dir.mkdir(exist_ok=True)
    query1_file = dummy_dir / "query1.sql"
    query2_file = dummy_dir / "query2.sql"
    with open(query1_file, "w") as f:
        f.write("SELECT 1")
    with open(query2_file, "w") as f:
        f.write("SELECT 2")

    # 1. Run query2 first
    db_connection.execute(
        "INSERT OR REPLACE INTO query_usage_log VALUES (?, ?, NOW())",
        ["query2.sql", user],
    )

    # 2. Run query1 second
    db_connection.execute(
        "INSERT OR REPLACE INTO query_usage_log VALUES (?, ?, NOW())",
        ["query1.sql", user],
    )

    # Get queries and check sort order
    # Access the wrapped function to bypass the @st.cache_data decorator
    all_queries = get_all_queries.__wrapped__(db_connection, user)

    # Clean up
    os.remove(query1_file)
    os.remove(query2_file)

    assert len(all_queries) == 2
    # query1 should be first as it was used more recently
    assert all_queries[0]["id"] == "query1.sql"
    assert all_queries[1]["id"] == "query2.sql"
