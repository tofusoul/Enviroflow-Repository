"""
Integration tests for MotherDuck database operations.

Tests that MotherDuck connection and data operations work correctly.
"""

import os

import polars as pl
import pytest

from enviroflow_app.elt.motherduck.md import MotherDuck


@pytest.mark.integration
class TestMotherDuckIntegration:
    """Test MotherDuck database integration."""

    @pytest.fixture
    def motherduck_conn(self):
        """Create a MotherDuck connection for testing."""
        token = os.getenv("MOTHERDUCK_TOKEN")
        if not token:
            pytest.skip("MOTHERDUCK_TOKEN environment variable not set")
        return MotherDuck(token=token, db_name="enviroflow")

    def test_motherduck_connection(self, motherduck_conn):
        """Test that we can connect to MotherDuck."""
        assert motherduck_conn.conn is not None

    def test_date_function_compatibility(self, motherduck_conn):
        """Test that date conversion functions work in MotherDuck."""
        conn = motherduck_conn.conn

        # Test CAST AS DATE
        result = conn.execute(
            "SELECT CAST('2023-01-01 12:34:56' AS DATE) as test_date"
        ).fetchall()
        assert len(result) == 1
        assert str(result[0][0]) == "2023-01-01"

        # Test ::DATE syntax
        result = conn.execute(
            "SELECT '2023-01-01 12:34:56'::DATE as test_date"
        ).fetchall()
        assert len(result) == 1
        assert str(result[0][0]) == "2023-01-01"

    def test_date_function_does_not_exist(self, motherduck_conn):
        """Test that DATE() function does not exist in this MotherDuck version."""
        conn = motherduck_conn.conn

        with pytest.raises(Exception) as exc_info:
            conn.execute("SELECT DATE('2023-01-01 12:34:56') as test_date").fetchall()

        assert "Scalar Function with name date does not exist" in str(exc_info.value)

    def test_job_cards_date_queries(self, motherduck_conn):
        """Test that job_cards queries work with proper date conversion."""
        conn = motherduck_conn.conn

        # Test approved jobs query
        try:
            result = conn.execute("""
                SELECT
                  card_title,
                  eqc_approved_date::DATE as eqc_approved_date,
                  status
                FROM job_cards
                WHERE eqc_approved_date IS NOT NULL
                ORDER BY eqc_approved_date DESC
                LIMIT 1
            """).fetchall()
            # Should not raise an exception
            assert isinstance(result, list)
        except Exception as e:
            pytest.fail(f"Approved jobs query failed: {e}")

        # Test jobs awaiting approval query
        try:
            result = conn.execute("""
                SELECT
                  card_title,
                  sent_to_customer_date::DATE as sent_to_customer_date,
                  status
                FROM job_cards
                WHERE status IN ('To NHC', 'Needs Followup')
                LIMIT 1
            """).fetchall()
            # Should not raise an exception
            assert isinstance(result, list)
        except Exception as e:
            pytest.fail(f"Jobs awaiting approval query failed: {e}")

    def test_motherduck_version_info(self, motherduck_conn):
        """Test that we can get MotherDuck version information."""
        conn = motherduck_conn.conn

        version = conn.execute("SELECT version()").fetchall()
        assert len(version) == 1
        assert "v1." in version[0][0]  # Should be a version like v1.2.2

    def test_get_table_list(self, motherduck_conn):
        """Test that we can get table list from MotherDuck."""
        tables = motherduck_conn.get_table_list()
        assert isinstance(tables, list)

    def test_save_and_retrieve_table(self, motherduck_conn):
        """Test that we can save and retrieve a test table."""
        # Create test data
        test_data = pl.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["test1", "test2", "test3"],
                "value": [10.5, 20.5, 30.5],
            }
        )

        table_name = "test_cli_integration"

        try:
            # Save table
            motherduck_conn.save_table(table_name, test_data)

            # Retrieve table
            retrieved_data = motherduck_conn.get_table(table_name)

            # Verify data matches
            assert retrieved_data.shape == test_data.shape
            assert set(retrieved_data.columns) == set(test_data.columns)

        finally:
            # Clean up test table
            try:
                motherduck_conn.run_sql(f"DROP TABLE IF EXISTS {table_name}")
            except Exception:
                pass  # Ignore cleanup errors

    def test_sql_execution(self, motherduck_conn):
        """Test that we can execute SQL queries."""
        # This should work even with empty database
        motherduck_conn.run_sql("SELECT 1 as test_value")
        # Just verify it doesn't crash
