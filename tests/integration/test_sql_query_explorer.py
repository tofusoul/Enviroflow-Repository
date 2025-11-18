"""
Integration tests for SQL Query Explorer functionality.

Tests that the simplified SQL Query Explorer can load and execute queries correctly.
"""

import os
from pathlib import Path
from typing import Dict, List, Any
import re

import pytest
import tomli

from enviroflow_app.elt.motherduck.md import MotherDuck


@pytest.mark.integration
class TestSQLQueryExplorer:
    """Test SQL Query Explorer functionality."""

    @pytest.fixture
    def motherduck_conn(self):
        """Create a MotherDuck connection for testing."""
        # Try to read from secrets file if available
        secrets_path = Path(".streamlit/secrets.toml")
        if secrets_path.exists():
            with open(secrets_path, "rb") as f:
                secrets = tomli.load(f)
                token = secrets["motherduck"]["token"]
                db_name = secrets["motherduck"]["db"]
        else:
            # Fallback to environment variables
            token = os.getenv("MOTHERDUCK_TOKEN")
            db_name = os.getenv("MOTHERDUCK_DB", "enviroflow")

        if not token:
            pytest.skip("MotherDuck token not available")

        return MotherDuck(token=token, db_name=db_name)

    def load_predefined_queries(self) -> List[Dict[str, Any]]:
        """Load predefined queries from the db_queries directory."""
        queries = []
        query_dir = Path("enviroflow_app/db_queries")

        if not query_dir.exists():
            return queries

        for file_path in query_dir.glob("*.sql*"):
            try:
                with open(file_path, "r") as f:
                    content = f.read()

                is_template = ".j2" in file_path.suffixes or "{{" in content
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

                if file_path.name in excluded_files:
                    continue

                # Skip queries with complex Jinja2 logic
                if "{% for" in content or "{% if" in content or ".pop(" in content:
                    continue

                # Skip CREATE/UPDATE/DELETE statements for safety
                content_upper = content.upper().strip()
                if any(
                    content_upper.startswith(stmt)
                    for stmt in [
                        "CREATE",
                        "UPDATE",
                        "DELETE",
                        "DROP",
                        "ALTER",
                        "INSERT",
                    ]
                ):
                    continue

                queries.append(
                    {
                        "name": file_path.stem.replace(".sql", "")
                        .replace("_", " ")
                        .title(),
                        "sql": content,
                        "is_template": is_template,
                        "variables": variables,
                        "type": "Pre-defined",
                        "file_path": str(file_path),
                    }
                )
            except Exception as e:
                print(f"Could not load query {file_path.name}: {e}")

        return queries

    def test_query_loading(self):
        """Test that predefined queries can be loaded from the db_queries directory."""
        queries = self.load_predefined_queries()

        assert len(queries) > 0, "Should find at least one query"

        # Check that queries have required fields
        for query in queries:
            assert "name" in query
            assert "sql" in query
            assert "is_template" in query
            assert "variables" in query
            assert "type" in query
            assert query["type"] == "Pre-defined"

    def test_template_detection(self):
        """Test that template queries are correctly identified."""
        queries = self.load_predefined_queries()

        template_queries = [q for q in queries if q["is_template"]]
        non_template_queries = [q for q in queries if not q["is_template"]]

        assert len(template_queries) > 0, "Should find at least one template query"
        assert (
            len(non_template_queries) > 0
        ), "Should find at least one non-template query"

        # Check that .j2 files are detected as templates
        for query in template_queries:
            if ".j2" in query["file_path"]:
                assert query[
                    "is_template"
                ], f"Query {query['name']} should be detected as template"

    def test_simple_query_execution(self, motherduck_conn):
        """Test that simple (non-template) queries can be executed."""
        queries = self.load_predefined_queries()
        simple_queries = [q for q in queries if not q["is_template"]]

        if not simple_queries:
            pytest.skip("No simple queries found to test")

        conn = motherduck_conn.conn

        # Test the first simple query
        query = simple_queries[0]
        try:
            result = conn.query(query["sql"]).pl()
            assert result is not None
            print(
                f"✅ Query '{query['name']}' executed successfully, returned {len(result)} rows"
            )
        except Exception as e:
            pytest.fail(f"Query '{query['name']}' failed: {e}")

    def test_approved_jobs_query_specifically(self, motherduck_conn):
        """Test the specific approved jobs query that was causing issues."""
        conn = motherduck_conn.conn

        # This is the corrected query with ::DATE syntax
        query = """
        select
          card_title,
          url,
          eqc_approved_date::DATE as eqc_approved_date,
          status,
          accepted_quote_value,
          submitted_quote_value,
          quote_value,
          report_by
        from job_cards
        where eqc_approved_date is not null
        order by eqc_approved_date desc
        limit 5
        """

        try:
            result = conn.query(query).pl()
            assert result is not None
            print(
                f"✅ Approved jobs query executed successfully, returned {len(result)} rows"
            )
        except Exception as e:
            pytest.fail(f"Approved jobs query failed: {e}")

    def test_template_query_with_variables(self, motherduck_conn):
        """Test that template queries work with provided variables."""
        queries = self.load_predefined_queries()
        template_queries = [q for q in queries if q["is_template"] and q["variables"]]

        if not template_queries:
            pytest.skip("No template queries with variables found to test")

        conn = motherduck_conn.conn

        # Test a template query with mock variables
        query = template_queries[0]

        # Create mock variables
        mock_vars = {}
        for var in query["variables"]:
            if "date" in var.lower():
                mock_vars[var] = "2023-01-01"
            elif "quote" in var.lower():
                mock_vars[var] = "QU-0001"
            else:
                mock_vars[var] = "test_value"

        # Render the template
        try:
            from jinja2 import Template

            template = Template(query["sql"])
            final_query = template.render(mock_vars)

            result = conn.query(final_query).pl()
            assert result is not None
            print(
                f"✅ Template query '{query['name']}' executed successfully with mock variables"
            )
        except Exception as e:
            pytest.fail(f"Template query '{query['name']}' failed: {e}")

    def test_motherduck_tables_exist(self, motherduck_conn):
        """Test that required tables exist in MotherDuck."""
        conn = motherduck_conn.conn

        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]

        # Check for tables that queries depend on
        required_tables = ["job_cards", "quotes"]

        for table in required_tables:
            assert (
                table in table_names
            ), f"Required table '{table}' not found in MotherDuck"

        print(
            f"✅ Found {len(table_names)} tables in MotherDuck, including required tables"
        )
