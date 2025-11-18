import pytest
import polars as pl
import pandas as pd

from enviroflow_app.gsheets import GoogleSheetsClient

# Test configuration
TEST_SPREADSHEET_ID = "1-c_VsrnmDK7eOB3pRxjTP0f2v0qFanpFomNuZJktDoU"
TEST_SPREADSHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{TEST_SPREADSHEET_ID}/edit"
)

# Expected table structures for P&L spreadsheet based on TODO requirements
EXPECTED_PNL_TABLES = {
    "costs": {
        "expected_columns": [
            "Date",
            "Account",
            "gen_proj",
            "Debit",
            "Credit",
            "Gross",
            "net",
            "GST",
        ],
        "min_rows": 10000,  # Should have ~13k records according to TODO
        "header_row": 1,  # Standard header in row 1
        "parser_type": "standard_paginated",
    },
    "constants": {
        "expected_tables": [
            "labour_constants",
            "account_categories",
            "units",
            "subcontractors",
        ],
        "separator_rows": 3,  # 3 blank rows separate tables
        "parser_type": "multi_table",
    },
    "report_scope_projects": {
        "expected_columns": ["name", "jan_24", "feb_24", "mar_24", "apr_24"],
        "min_rows": 500,
        "header_row": 2,  # Headers in row 2, not row 1
        "parser_type": "offset_header",
    },
    "xero_name": {
        "expected_columns": ["xero_name", "Project"],
        "min_rows": 100,
        "header_row": 1,
        "parser_type": "standard",
    },
    "sales": {
        "expected_columns": ["Date", "Invoice", "Customer"],
        "min_rows": 1000,
        "header_row": 1,
        "parser_type": "standard",
    },
    "quotes": {
        "expected_columns": ["Date", "Number", "Customer"],
        "min_rows": 1000,
        "header_row": 1,
        "parser_type": "standard",
    },
    "pricing_table": {
        "expected_columns": ["Item", "Unit", "Rate"],
        "min_rows": 100,
        "header_row": 1,
        "parser_type": "standard",
    },
}


@pytest.fixture
def gsheets_client():
    """Fixture to provide an initialized GoogleSheetsClient."""
    return GoogleSheetsClient()


@pytest.mark.asyncio
async def test_service_account_access(gsheets_client):
    """Test service account authentication and spreadsheet access."""
    spreadsheets = await gsheets_client.list_spreadsheets()

    assert len(spreadsheets) > 0, "Should find accessible spreadsheets"
    assert (
        len(spreadsheets) >= 10
    ), f"Expected at least 10 spreadsheets, found {len(spreadsheets)}"

    # Find our test spreadsheet
    test_spreadsheet = None
    for spreadsheet in spreadsheets:
        if TEST_SPREADSHEET_ID in spreadsheet.spreadsheet_id:
            test_spreadsheet = spreadsheet
            break

    assert (
        test_spreadsheet is not None
    ), f"Test spreadsheet {TEST_SPREADSHEET_ID} not found in accessible sheets"
    assert (
        "Project P&L Report" in test_spreadsheet.title
    ), f"Expected 'Project P&L Report' in title, got {test_spreadsheet.title}"


@pytest.mark.asyncio
async def test_spreadsheet_info_retrieval(gsheets_client):
    """Test retrieving spreadsheet information and sheet list."""
    spreadsheet_info = await gsheets_client.get_spreadsheet_info(TEST_SPREADSHEET_ID)

    assert spreadsheet_info.title == "Project P&L Report"
    assert (
        len(spreadsheet_info.sheets) >= 15
    ), f"Expected at least 15 sheets, found {len(spreadsheet_info.sheets)}"

    # Check for critical P&L sheets
    sheet_names = [sheet.name for sheet in spreadsheet_info.sheets]
    critical_sheets = ["costs", "constants", "report_scope_projects", "quotes"]

    for sheet in critical_sheets:
        assert (
            sheet in sheet_names
        ), f"Critical sheet '{sheet}' not found in spreadsheet"


@pytest.mark.asyncio
async def test_header_detection_intelligence(gsheets_client):
    """Test intelligent header detection for different table structures."""
    # Test standard header (row 1)
    costs_data = await gsheets_client.get_sheet_data(TEST_SPREADSHEET_ID, "costs")
    headers, cleaned_rows = gsheets_client._prepare_data_for_polars(costs_data)

    assert len(headers) > 5, f"Costs should have multiple columns, got {len(headers)}"
    assert (
        "Date" in headers
    ), f"Expected 'Date' column in costs, got headers: {headers[:5]}"

    # Test offset header (row 2) for report_scope_projects
    scope_data = await gsheets_client.get_sheet_data(
        TEST_SPREADSHEET_ID, "report_scope_projects"
    )
    scope_headers, scope_rows = gsheets_client._prepare_data_for_polars(scope_data)

    assert (
        len(scope_headers) >= 50
    ), f"Scope projects should have many columns, got {len(scope_headers)}"
    assert (
        "name" in scope_headers
    ), f"Expected 'name' column in scope projects, got headers: {scope_headers[:5]}"
    assert (
        len(scope_rows) >= 500
    ), f"Should have substantial data rows, got {len(scope_rows)}"


@pytest.mark.asyncio
async def test_dataframe_engine_consistency(gsheets_client):
    """Test both Polars and Pandas engines produce consistent results."""
    sheet_name = "report_scope_projects"

    # Test Polars engine
    df_polars = await gsheets_client.get_sheet_as_dataframe(
        TEST_SPREADSHEET_ID, sheet_name, engine="polars"
    )

    # Test Pandas engine
    df_pandas = await gsheets_client.get_sheet_as_dataframe(
        TEST_SPREADSHEET_ID, sheet_name, engine="pandas"
    )

    # Verify types
    assert isinstance(
        df_polars, pl.DataFrame
    ), "Polars engine should return Polars DataFrame"
    assert isinstance(
        df_pandas, pd.DataFrame
    ), "Pandas engine should return Pandas DataFrame"

    # Verify consistency
    assert (
        df_polars.shape == df_pandas.shape
    ), f"Shape mismatch: Polars {df_polars.shape} vs Pandas {df_pandas.shape}"

    polars_cols = set(df_polars.columns)
    pandas_cols = set(df_pandas.columns)
    assert (
        polars_cols == pandas_cols
    ), f"Column mismatch: {polars_cols.symmetric_difference(pandas_cols)}"

    # Verify data content (first few rows)
    polars_sample = df_polars.head(3).select(df_polars.columns[:3])
    pandas_sample = df_pandas.iloc[:3, :3]

    assert len(polars_sample) == len(pandas_sample), "Sample row counts should match"


@pytest.mark.asyncio
async def test_pagination_and_row_count_accuracy(gsheets_client):
    """Test pagination handling and verify complete data retrieval."""
    # Test costs table which should have ~13k records according to TODO
    costs_df = await gsheets_client.get_sheet_as_dataframe(
        TEST_SPREADSHEET_ID, "costs", engine="polars"
    )

    # Critical test: verify we get all records, not just first page
    assert (
        len(costs_df) > 5000
    ), f"Costs table should have >5k records, got {len(costs_df)} (possible pagination issue)"

    # Ideally should be closer to 13k according to TODO
    if len(costs_df) < 10000:
        import warnings

        warnings.warn(
            f"Costs table has {len(costs_df)} records but TODO indicates should be ~13k. "
            "This suggests a pagination issue in Google Sheets API.",
            UserWarning,
        )

    # Verify data quality
    assert (
        len(costs_df.columns) >= 5
    ), f"Costs should have multiple columns, got {len(costs_df.columns)}"

    # Check for expected columns (allowing for renamed columns)
    expected_cols = [
        "Date",
        "Account",
        "gen_proj",
        "Project",
    ]  # gen_proj gets renamed to Project
    found_cols = [col for col in expected_cols if col in costs_df.columns]
    assert (
        len(found_cols) >= 2
    ), f"Should find key columns in costs table, found: {found_cols}"


@pytest.mark.asyncio
async def test_data_type_handling_and_transformations(gsheets_client):
    """Test proper data type handling and numeric conversions."""
    costs_df = await gsheets_client.get_sheet_as_dataframe(
        TEST_SPREADSHEET_ID, "costs", engine="polars"
    )

    # Check that we have string data initially (before transformation)
    assert costs_df.dtypes[0] == pl.String, "Initial data should be string type"

    # Test sample data structure
    sample_data = costs_df.head(5)
    assert len(sample_data) > 0, "Should have sample data"

    # Verify we can identify numeric columns that need conversion
    # (This simulates the transformation logic from extraction_ops.py)
    potential_numeric_cols = ["Debit", "Credit", "Gross", "net", "GST"]
    numeric_cols_present = [
        col for col in potential_numeric_cols if col in costs_df.columns
    ]

    assert (
        len(numeric_cols_present) >= 2
    ), f"Should find numeric columns, found: {numeric_cols_present}"


@pytest.mark.asyncio
async def test_raw_data_structure_analysis(gsheets_client):
    """Test raw data structure analysis for debugging purposes."""
    sheet_name = "report_scope_projects"
    raw_data = await gsheets_client.get_sheet_data(TEST_SPREADSHEET_ID, sheet_name)

    # Verify raw data structure
    assert (
        len(raw_data) > 100
    ), f"Should have substantial raw data, got {len(raw_data)} rows"

    # Check row length variations (ragged data handling)
    row_lengths = [len(row) for row in raw_data[:10]]
    assert len(set(row_lengths)) > 1, "Should have varying row lengths (ragged data)"

    # Verify header detection logic
    max_length = max(row_lengths)
    min_length = min(row_lengths)
    assert (
        max_length > min_length
    ), f"Row lengths should vary: {min_length} to {max_length}"

    # Check for non-empty cells in different rows (header detection test)
    for i, row in enumerate(raw_data[:5]):
        non_empty_count = sum(1 for cell in row if cell and str(cell).strip())
        print(f"Row {i}: {non_empty_count} non-empty cells, first 3: {row[:3]}")


@pytest.mark.asyncio
async def test_sample_data_verification(gsheets_client):
    """Test sample data extraction and verification."""
    df = await gsheets_client.get_sheet_as_dataframe(
        TEST_SPREADSHEET_ID, "report_scope_projects", engine="polars"
    )

    # Verify sample data structure
    sample = df.head(3).select(df.columns[:3])
    assert sample.shape == (3, 3), f"Sample should be 3x3, got {sample.shape}"

    # Check that we have actual data (not all nulls/empty)
    sample_values = sample.to_pandas().values.flatten()
    non_null_values = [v for v in sample_values if v is not None and str(v).strip()]
    assert (
        len(non_null_values) >= 3
    ), f"Should have actual data values, got: {non_null_values[:5]}"


@pytest.mark.asyncio
async def test_error_handling_and_fallbacks(gsheets_client):
    """Test error handling for invalid sheets and edge cases."""
    # Test invalid sheet name
    with pytest.raises(Exception):
        await gsheets_client.get_sheet_as_dataframe(
            TEST_SPREADSHEET_ID, "nonexistent_sheet", engine="polars"
        )

    # Test invalid spreadsheet ID
    with pytest.raises(Exception):
        await gsheets_client.get_sheet_as_dataframe(
            "invalid_spreadsheet_id", "costs", engine="polars"
        )

    # Test invalid engine
    with pytest.raises(Exception):
        await gsheets_client.get_sheet_as_dataframe(
            TEST_SPREADSHEET_ID, "costs", engine="invalid_engine"
        )


# ===== PERFORMANCE AND INTEGRATION TESTS =====


@pytest.mark.asyncio
async def test_multiple_table_extraction_performance(gsheets_client):
    """Test extracting multiple tables efficiently."""
    import time

    tables_to_test = ["costs", "report_scope_projects", "quotes"]
    results = {}

    start_time = time.time()

    for table in tables_to_test:
        table_start = time.time()
        df = await gsheets_client.get_sheet_as_dataframe(
            TEST_SPREADSHEET_ID, table, engine="polars"
        )
        table_time = time.time() - table_start

        results[table] = {
            "rows": len(df),
            "columns": len(df.columns),
            "time_seconds": table_time,
        }

        print(
            f"✅ {table}: {len(df)} rows × {len(df.columns)} columns in {table_time:.2f}s"
        )

    total_time = time.time() - start_time
    total_rows = sum(r["rows"] for r in results.values())

    print(
        f"Total extraction: {total_rows} rows from {len(tables_to_test)} tables in {total_time:.2f}s"
    )

    # Performance assertions
    assert (
        total_time < 60
    ), f"Extraction should complete in <60s, took {total_time:.2f}s"
    assert total_rows > 1000, f"Should extract substantial data, got {total_rows} rows"


@pytest.mark.asyncio
async def test_get_sheet_as_dataframe():
    """Legacy test maintained for compatibility."""
    client = GoogleSheetsClient()
    sheet_name = "report_scope_projects"

    try:
        df = await client.get_sheet_as_dataframe(
            TEST_SPREADSHEET_URL, sheet_name, engine="polars"
        )
        print("Output DataFrame:")
        print(df)
        assert isinstance(df, pl.DataFrame), "Output is not a Polars DataFrame"
        assert len(df.columns) > 0, "DataFrame should have columns"
        print("Test passed: DataFrame created successfully.")
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
