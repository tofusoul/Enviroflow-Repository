import pytest
from unittest.mock import MagicMock, patch, mock_open
import pandas as pd
from datetime import datetime
import polars as pl

# Mock streamlit before importing helpers
import sys

sys.modules["streamlit"] = MagicMock()

from enviroflow_app.helpers.query_helpers import (
    get_all_queries,
    execute_query,
    save_custom_query,
)


@pytest.fixture
def mock_db_connection():
    """Fixture for a mocked DuckDB connection."""
    mock_conn = MagicMock()
    return mock_conn


def test_get_all_queries_sorting_and_merging(mock_db_connection):
    """
    Tests that queries from filesystem and DB are merged and sorted correctly by most recently used.
    """
    # Mock filesystem reads
    mock_sql_content = "SELECT * FROM table1"
    mock_j2_content = "SELECT * FROM table2 WHERE date = '{{ my_date }}'"
    m = mock_open(read_data=mock_sql_content)
    m.side_effect = [
        mock_open(read_data=mock_sql_content).return_value,
        mock_open(read_data=mock_j2_content).return_value,
    ]

    # Mock database responses
    custom_queries_df = pd.DataFrame(
        {
            "id": ["uuid1"],
            "name": ["My Custom Query"],
            "sql_template": ["SELECT * FROM custom_table"],
            "is_template": [False],
            "last_used_at": [datetime(2023, 1, 1, 12, 0, 0)],
            "created_by": ["user@test.com"],
        }
    )
    usage_log_df = pd.DataFrame(
        {
            "query_name": ["predefined.sql"],
            "last_used_at": [datetime(2023, 5, 1, 12, 0, 0)],
        }
    )
    mock_db_connection.execute.side_effect = [
        MagicMock(fetchdf=lambda: custom_queries_df),  # For custom_queries
        MagicMock(fetchdf=lambda: usage_log_df),  # For query_usage_log
    ]

    with patch("pathlib.Path.glob") as mock_glob, patch("builtins.open", m):
        mock_glob.return_value = [
            MagicMock(suffixes=[".sql"], name="predefined.sql", stem="predefined"),
            MagicMock(
                suffixes=[".sql", ".j2"], name="templated.sql.j2", stem="templated.sql"
            ),
        ]

        # Access the wrapped function to bypass the @st.cache_data decorator
        queries = get_all_queries.__wrapped__(mock_db_connection, "user@test.com")

        assert len(queries) == 3
        # Check sorting: predefined (used May 1), custom (used Jan 1), templated (never used)
        assert queries[0]["name"] == "Predefined"
        assert queries[0]["last_used_at"] == datetime(2023, 5, 1, 12, 0, 0)
        assert queries[1]["name"] == "My Custom Query"
        assert queries[2]["name"] == "Templated"
        assert queries[2]["last_used_at"] is None
        assert queries[1]["variables"] == []
        assert queries[2]["variables"] == ["my_date"]


def test_execute_query_success(mock_db_connection):
    """Tests successful query execution."""
    expected_df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
    mock_db_connection.execute.return_value.pl.return_value = expected_df.to_pandas()

    result = execute_query(mock_db_connection, "SELECT * FROM test")

    assert isinstance(result, pl.DataFrame)
    assert result.to_pandas().equals(expected_df.to_pandas())


def test_execute_query_template_render(mock_db_connection):
    """Tests that Jinja2 templates are rendered before execution."""
    query = "SELECT * FROM test WHERE val = '{{ my_val }}'"

    execute_query(mock_db_connection, query, {"my_val": "hello"})

    # Check that the executed query was the rendered one
    mock_db_connection.execute.assert_called_with(
        "SELECT * FROM test WHERE val = 'hello'"
    )


def test_save_custom_query_fails_validation(mock_db_connection):
    """Tests that a query failing live validation is not saved."""
    # Mock the execute_query function to return an error string
    with patch("enviroflow_app.helpers.query_helpers.execute_query") as mock_execute:
        mock_execute.return_value = "Database error: Table not found"

        success, message = save_custom_query(
            mock_db_connection,
            "Bad Query",
            "SELECT * FROM non_existent_table",
            "user@test.com",
        )

        assert not success
        assert "Query failed validation" in message
        # Ensure no attempt was made to insert into the DB
        mock_db_connection.execute.assert_not_called()


def test_save_custom_query_success(mock_db_connection):
    """Tests that a valid query is successfully saved."""
    with (
        patch("enviroflow_app.helpers.query_helpers.execute_query") as mock_execute,
        patch("enviroflow_app.helpers.query_helpers.get_db_schema") as mock_get_schema,
    ):
        # Mock successful validation
        mock_execute.return_value = pl.DataFrame()
        mock_get_schema.return_value = {"my_table": ["col1"]}

        success, message = save_custom_query(
            mock_db_connection, "Good Query", "SELECT * FROM my_table", "user@test.com"
        )

        assert success
        assert "Query saved successfully" in message
        # Check that the INSERT statement was called
        mock_db_connection.execute.assert_called_once()
        call_args = mock_db_connection.execute.call_args[0]
        assert "INSERT INTO custom_queries" in call_args[0]
