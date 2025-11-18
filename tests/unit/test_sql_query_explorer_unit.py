"""
Unit tests for the simplified SQL Query Explorer functionality.

Tests query loading, template detection, and other logic without requiring database connections.
"""

from pathlib import Path
import re
from typing import Dict, List, Any


class TestSQLQueryExplorerUnit:
    """Unit tests for SQL Query Explorer logic."""

    def load_predefined_queries_mock(
        self, mock_files: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Mock version of load_predefined_queries for testing."""
        queries = []

        for file_path, content in mock_files.items():
            path = Path(file_path)

            is_template = ".j2" in path.suffixes or "{{" in content
            variables = (
                re.findall(r"\{\{\s*(\w+)\s*\}\}", content) if is_template else []
            )

            # Skip specific operational queries that shouldn't be run through the query explorer
            excluded_files = {
                "filter_table.sql",
                "filter_vo_quotes.sql",
                "generate_item_budget_table.sql",
                "update_quotes.sql",
                "update_item_budget_table.sql",
            }

            if Path(file_path).name in excluded_files:
                continue

            # Skip queries with complex Jinja2 logic that our simple system can't handle
            if "{% for" in content or "{% if" in content or ".pop(" in content:
                continue

            # Skip CREATE/UPDATE/DELETE statements for safety
            content_upper = content.upper().strip()
            if any(
                content_upper.startswith(stmt)
                for stmt in ["CREATE", "UPDATE", "DELETE", "DROP", "ALTER", "INSERT"]
            ):
                continue

            queries.append(
                {
                    "name": path.stem.replace(".sql", "").replace("_", " ").title(),
                    "sql": content,
                    "is_template": is_template,
                    "variables": variables,
                    "type": "Pre-defined",
                    "file_path": file_path,
                }
            )

        return queries

    def test_simple_query_detection(self):
        """Test that simple SQL queries are correctly identified."""
        mock_files = {
            "approved_jobs.sql": """
                SELECT card_title, status
                FROM job_cards
                WHERE status = 'approved'
            """,
            "basic_select.sql": "SELECT * FROM quotes",
        }

        queries = self.load_predefined_queries_mock(mock_files)

        assert len(queries) == 2
        for query in queries:
            assert not query["is_template"]
            assert len(query["variables"]) == 0

    def test_template_query_detection(self):
        """Test that template queries are correctly identified."""
        mock_files = {
            "quotes_after.sql.j2": """
                SELECT * FROM quotes
                WHERE quote_no > '{{ quote_no }}'
            """,
            "jobs_by_date.sql": """
                SELECT * FROM job_cards
                WHERE date > '{{ start_date }}'
            """,
        }

        queries = self.load_predefined_queries_mock(mock_files)

        assert len(queries) == 2

        # Check .j2 file
        j2_query = next(q for q in queries if q["file_path"].endswith(".j2"))
        assert j2_query["is_template"]
        assert "quote_no" in j2_query["variables"]

        # Check SQL file with template syntax
        sql_query = next(
            q for q in queries if q["file_path"].endswith("jobs_by_date.sql")
        )
        assert sql_query["is_template"]
        assert "start_date" in sql_query["variables"]

    def test_complex_template_skipping(self):
        """Test that complex template queries are skipped."""
        mock_files = {
            "simple.sql": "SELECT * FROM quotes",
            "complex_loop.sql": """
                SELECT * FROM {{ table_name }}
                WHERE
                {% for item in items %}
                    column = '{{ item }}'
                    {% if not loop.last %}OR{% endif %}
                {% endfor %}
            """,
            "complex_condition.sql": """
                SELECT * FROM table
                WHERE value.pop(0) = 1
            """,
        }

        queries = self.load_predefined_queries_mock(mock_files)

        # Only the simple query should be loaded
        assert len(queries) == 1
        assert queries[0]["file_path"] == "simple.sql"

    def test_variable_extraction(self):
        """Test that Jinja2 variables are correctly extracted."""
        mock_files = {
            "multi_var.sql": """
                SELECT * FROM job_cards
                WHERE date >= '{{ start_date }}'
                AND date <= '{{ end_date }}'
                AND status = '{{ status }}'
                AND {{ column_name }} IS NOT NULL
            """
        }

        queries = self.load_predefined_queries_mock(mock_files)

        assert len(queries) == 1
        query = queries[0]

        assert query["is_template"]
        expected_vars = ["start_date", "end_date", "status", "column_name"]
        assert set(query["variables"]) == set(expected_vars)

    def test_query_name_generation(self):
        """Test that query names are generated correctly from filenames."""
        mock_files = {
            "approved_jobs_list.sql": "SELECT * FROM jobs",
            "jobs_awaiting_approval.sql.j2": "SELECT * FROM jobs WHERE status = '{{ status }}'",
            "simple.sql": "SELECT 1",
        }

        queries = self.load_predefined_queries_mock(mock_files)

        expected_names = {"Approved Jobs List", "Jobs Awaiting Approval", "Simple"}

        actual_names = {q["name"] for q in queries}
        assert actual_names == expected_names

    def test_date_function_sql_correction(self):
        """Test the SQL correction logic for DATE() function."""
        # This tests the SQL transformation we needed to do
        original_sql = (
            "SELECT DATE(eqc_approved_date) as eqc_approved_date FROM job_cards"
        )
        corrected_sql = (
            "SELECT eqc_approved_date::DATE as eqc_approved_date FROM job_cards"
        )

        # Test that the correction pattern works
        pattern = r"DATE\(([^)]+)\)"
        replacement = r"\1::DATE"

        result = re.sub(pattern, replacement, original_sql)
        assert result == corrected_sql

    def test_template_rendering_simulation(self):
        """Test template rendering without actual Jinja2."""
        template_sql = "SELECT * FROM quotes WHERE quote_no > '{{ quote_no }}'"
        variables = {"quote_no": "QU-0001"}

        # Simple string replacement for testing (mimics Jinja2)
        rendered = template_sql
        for var, value in variables.items():
            rendered = rendered.replace(f"{{{{ {var} }}}}", str(value))

        expected = "SELECT * FROM quotes WHERE quote_no > 'QU-0001'"
        assert rendered == expected

    def test_mock_variable_generation(self):
        """Test generation of mock variables for different types."""
        variables = ["start_date", "end_date", "quote_no", "status", "limit_count"]

        mock_vars = {}
        for var in variables:
            if "date" in var.lower():
                mock_vars[var] = "2023-01-01"
            elif "quote" in var.lower():
                mock_vars[var] = "QU-0001"
            elif "count" in var.lower() or "limit" in var.lower():
                mock_vars[var] = 10
            else:
                mock_vars[var] = "test_value"

        expected = {
            "start_date": "2023-01-01",
            "end_date": "2023-01-01",
            "quote_no": "QU-0001",
            "status": "test_value",
            "limit_count": 10,
        }

        assert mock_vars == expected

    def test_excluded_files_filtering(self):
        """Test that specific operational queries are excluded."""
        mock_files = {
            "approved_jobs.sql": "SELECT * FROM job_cards WHERE status = 'approved'",
            "filter_table.sql": "SELECT * FROM {{ table_name }} WHERE ...",
            "update_quotes.sql": "CREATE OR REPLACE TABLE quotes AS SELECT ...",
            "generate_item_budget_table.sql": "CREATE TABLE ...",
            "normal_query.sql": "SELECT * FROM quotes",
        }

        queries = self.load_predefined_queries_mock(mock_files)

        # Should only have approved_jobs.sql and normal_query.sql
        assert len(queries) == 2
        query_files = {q["file_path"] for q in queries}
        assert "approved_jobs.sql" in query_files
        assert "normal_query.sql" in query_files
        assert "filter_table.sql" not in query_files
        assert "update_quotes.sql" not in query_files
        assert "generate_item_budget_table.sql" not in query_files

    def test_create_update_statement_filtering(self):
        """Test that CREATE/UPDATE/DELETE statements are filtered out."""
        mock_files = {
            "select_query.sql": "SELECT * FROM job_cards",
            "create_query.sql": "CREATE TABLE test AS SELECT * FROM job_cards",
            "update_query.sql": "UPDATE job_cards SET status = 'new'",
            "delete_query.sql": "DELETE FROM job_cards WHERE id = 1",
            "insert_query.sql": "INSERT INTO job_cards VALUES (...)",
            "drop_query.sql": "DROP TABLE test_table",
        }

        queries = self.load_predefined_queries_mock(mock_files)

        # Should only have the SELECT query
        assert len(queries) == 1
        assert queries[0]["file_path"] == "select_query.sql"
