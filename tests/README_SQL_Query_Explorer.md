# SQL Query Explorer Test Documentation

This document describes the test suite for the simplified SQL Query Explorer functionality.

## Test Structure

### Unit Tests
**File**: `tests/unit/test_sql_query_explorer_unit.py`

These tests validate the query loading and processing logic without requiring database connections:

- **Query Loading**: Tests that SQL files are correctly loaded from the `db_queries` directory
- **Template Detection**: Validates that Jinja2 template queries (`.j2` files and files containing `{{}}`) are correctly identified
- **Complex Template Skipping**: Ensures queries with complex Jinja2 logic (`{% for %}`, `{% if %}`, `.pop()`) are skipped
- **Variable Extraction**: Tests that template variables are correctly extracted from query content
- **Name Generation**: Validates that human-readable names are generated from filenames
- **SQL Correction**: Tests the DATE() function correction logic (DATE() → ::DATE)
- **Template Rendering**: Simulates Jinja2 template rendering for testing
- **Mock Variables**: Tests generation of appropriate mock values for different variable types

### Integration Tests
**File**: `tests/integration/test_sql_query_explorer.py`

These tests validate the full functionality with real MotherDuck connections:

- **Query Execution**: Tests that simple (non-template) queries can be executed against MotherDuck
- **Template Queries**: Tests that template queries work with provided variables
- **Specific Query Tests**: Validates the corrected "approved jobs" query that was causing DATE() function issues
- **Table Existence**: Ensures required tables exist in the MotherDuck database
- **Real Data Tests**: Uses actual database content to validate query results

**File**: `tests/integration/test_motherduck_integration.py` (enhanced)

Added tests for MotherDuck-specific functionality:

- **DATE Function Compatibility**: Tests that `CAST(...AS DATE)` and `::DATE` work correctly
- **DATE Function Non-existence**: Validates that `DATE()` function doesn't exist in this DuckDB version
- **Job Cards Queries**: Tests the corrected date queries against real data
- **Version Information**: Captures MotherDuck/DuckDB version info for debugging

## Key Issues Discovered and Tested

### DATE() Function Issue
**Problem**: The original queries used `DATE(column_name)` which doesn't exist in DuckDB v1.2.2
**Solution**: Changed to `column_name::DATE` syntax
**Tests**:
- `test_date_function_compatibility()` - validates working alternatives
- `test_date_function_does_not_exist()` - confirms the issue
- `test_job_cards_date_queries()` - tests corrected queries

### Template Query Complexity
**Problem**: Some queries contain complex Jinja2 logic that the simple interface can't handle
**Solution**: Skip queries with `{% for %}`, `{% if %}`, or `.pop()` constructs
**Tests**: `test_complex_template_skipping()` validates this filtering

### Query Loading and Processing
**Problem**: Need reliable query discovery and metadata extraction
**Solution**: Systematic file scanning with regex-based variable extraction
**Tests**: Multiple unit tests validate each aspect of query processing

### Operational Query Exclusion
**Problem**: Certain queries are operational/administrative and shouldn't be run through the query explorer
**Solution**: Exclude specific files and any CREATE/UPDATE/DELETE statements
**Excluded Files**: `filter_table.sql`, `filter_vo_quotes.sql`, `generate_item_budget_table.sql`, `update_quotes.sql`, `update_item_budget_table.sql`
**Tests**:
- `test_excluded_files_filtering()` - validates specific file exclusion
- `test_create_update_statement_filtering()` - validates DDL/DML statement exclusion

## Running Tests

```bash
# Run all SQL Query Explorer tests
pytest tests/unit/test_sql_query_explorer_unit.py tests/integration/test_sql_query_explorer.py -v

# Run just unit tests (no DB required)
pytest tests/unit/test_sql_query_explorer_unit.py -v

# Run just integration tests (requires MotherDuck access)
pytest tests/integration/test_sql_query_explorer.py -v
```

## Test Data Requirements

Integration tests require:
- MotherDuck connection configured in `.streamlit/secrets.toml`
- Tables: `job_cards`, `quotes` (minimum)
- Some test data in those tables for meaningful results

The tests are designed to be non-destructive and read-only.
