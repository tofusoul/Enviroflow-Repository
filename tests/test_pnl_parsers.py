"""
Test suite for flexible Google Sheets parsing system and P&L table extraction.

This module tests the injectable parser framework and P&L-specific extraction
functionality with comprehensive validation.
"""

import pytest
import polars as pl
import pandas as pd

from enviroflow_app.gsheets.parsers import (
    ParsingConfig,
    StandardTableParser,
    OffsetHeaderParser,
    MultiTableParser,
    PaginatedTableParser,
    ParserFactory,
    create_pnl_parser,
    PNL_PARSER_CONFIGS,
    PNL_PARSER_TYPES,
)
from enviroflow_app.gsheets.pnl_client import PnLGoogleSheetsClient

# Test data constants
TEST_SPREADSHEET_ID = "1-c_VsrnmDK7eOB3pRxjTP0f2v0qFanpFomNuZJktDoU"
REQUIRED_PNL_TABLES = [
    "costs",
    "constants",
    "report_scope_projects",
    "xero_name",
    "sales",
    "quotes",
    "pricing_table",
]


# ===== PARSER UNIT TESTS =====


def test_parser_factory():
    """Test parser factory creates correct parser types."""
    config = ParsingConfig()

    # Test each parser type
    standard_parser = ParserFactory.create_parser("standard", config)
    assert isinstance(standard_parser, StandardTableParser)

    offset_parser = ParserFactory.create_parser("offset_header", config)
    assert isinstance(offset_parser, OffsetHeaderParser)

    multi_parser = ParserFactory.create_parser("multi_table", config)
    assert isinstance(multi_parser, MultiTableParser)

    paginated_parser = ParserFactory.create_parser("standard_paginated", config)
    assert isinstance(paginated_parser, PaginatedTableParser)

    # Test invalid parser type
    with pytest.raises(ValueError):
        ParserFactory.create_parser("invalid_type", config)


def test_pnl_parser_configurations():
    """Test P&L parser configurations are properly defined."""
    # Verify all required tables have configurations
    for table_name in REQUIRED_PNL_TABLES:
        assert table_name in PNL_PARSER_CONFIGS, f"Missing config for {table_name}"
        assert table_name in PNL_PARSER_TYPES, f"Missing parser type for {table_name}"

        config = PNL_PARSER_CONFIGS[table_name]
        assert isinstance(config, ParsingConfig)
        assert config.header_row >= 1, f"Invalid header row for {table_name}"
        assert config.expected_min_rows > 0, f"Invalid min rows for {table_name}"


def test_create_pnl_parser():
    """Test P&L parser creation with pre-configured settings."""
    # Test each P&L table parser
    for table_name in REQUIRED_PNL_TABLES:
        parser = create_pnl_parser(table_name)
        assert parser is not None
        assert hasattr(parser, "parse")
        assert hasattr(parser, "validate")

        # Verify parser type matches expected
        expected_type = PNL_PARSER_TYPES[table_name]
        if expected_type == "standard":
            assert isinstance(parser, StandardTableParser)
        elif expected_type == "offset_header":
            assert isinstance(parser, OffsetHeaderParser)
        elif expected_type == "multi_table":
            assert isinstance(parser, MultiTableParser)
        elif expected_type == "standard_paginated":
            assert isinstance(parser, PaginatedTableParser)

    # Test invalid table name
    with pytest.raises(ValueError):
        create_pnl_parser("invalid_table")


def test_parsing_config():
    """Test parsing configuration validation."""
    # Valid config
    config = ParsingConfig(
        header_row=1,
        expected_min_rows=100,
        expected_columns=["col1", "col2"],
        auto_detect_headers=True,
    )
    assert config.header_row == 1
    assert config.expected_min_rows == 100
    assert config.expected_columns == ["col1", "col2"]
    assert config.auto_detect_headers is True

    # Test defaults
    default_config = ParsingConfig()
    assert default_config.header_row == 1
    assert default_config.max_blank_rows == 3
    assert default_config.expected_min_rows == 10


def test_standard_parser():
    """Test standard table parser with mock data."""
    # Mock data: header row + data rows
    mock_data = [
        ["Name", "Age", "City"],  # Header row
        ["Alice", "25", "NYC"],
        ["Bob", "30", "LA"],
        ["Charlie", "35", ""],  # Missing data
    ]

    config = ParsingConfig(expected_min_rows=2)
    parser = StandardTableParser(config)

    result = parser.parse(mock_data, "test_table")

    assert result.name == "test_table"
    assert result.row_count == 3
    assert result.column_count == 3
    assert result.headers == ["Name", "Age", "City"]
    assert result.parser_used == "standard"
    assert isinstance(result.data, pl.DataFrame)

    # Test validation
    assert parser.validate(result) is True


def test_offset_header_parser():
    """Test offset header parser for tables with headers not in row 1."""
    # Mock data: empty row, then header, then data
    mock_data = [
        ["", "", ""],  # Empty first row
        ["Name", "Value", "Status"],  # Header in row 2
        ["Item1", "100", "Active"],
        ["Item2", "200", "Inactive"],
    ]

    config = ParsingConfig(header_row=2, auto_detect_headers=False, expected_min_rows=1)
    parser = OffsetHeaderParser(config)

    result = parser.parse(mock_data, "offset_test")

    assert result.name == "offset_test"
    assert result.row_count == 2
    assert result.column_count == 3
    assert result.headers == ["Name", "Value", "Status"]
    assert result.parser_used == "offset_header"
    assert result.metadata["header_row"] == 2
    assert result.metadata["skipped_rows"] == 1


def test_multi_table_parser():
    """Test multi-table parser for sheets with multiple tables."""
    # Mock data: two tables separated by blank rows
    mock_data = [
        # Table 1
        ["Col1", "Col2"],
        ["A", "B"],
        ["C", "D"],
        # Separator (3 blank rows)
        ["", ""],
        ["", ""],
        ["", ""],
        # Table 2
        ["Name", "Score"],
        ["X", "10"],
        ["Y", "20"],
    ]

    config = ParsingConfig(max_blank_rows=3, expected_min_rows=1)
    parser = MultiTableParser(config)

    result = parser.parse(mock_data, "multi_test")

    assert result.parser_used == "multi_table"
    assert "table_count" in result.metadata
    assert result.metadata["table_count"] >= 1  # Should find at least one table
    assert "table_boundaries" in result.metadata


def test_paginated_parser():
    """Test paginated parser detects potential pagination issues."""
    # Mock data with row count near pagination boundary
    mock_data = [["Col1", "Col2"]]
    # Add 999 data rows (near 1000 page boundary)
    for i in range(999):
        mock_data.append([f"Data{i}", f"Value{i}"])

    config = ParsingConfig(pagination_size=1000, expected_min_rows=500)
    parser = PaginatedTableParser(config)

    result = parser.parse(mock_data, "paginated_test")

    assert result.parser_used == "paginated"
    assert "likely_paginated" in result.metadata
    assert result.metadata["likely_paginated"] is True  # Should detect pagination
    assert result.row_count == 999


# ===== P&L CLIENT INTEGRATION TESTS =====


@pytest.fixture
def pnl_client():
    """Fixture to provide a P&L Google Sheets client."""
    # The client performs async I/O in its methods, but construction is sync
    return PnLGoogleSheetsClient()


@pytest.mark.asyncio
async def test_pnl_client_initialization(pnl_client):
    """Test P&L client initializes correctly."""
    assert pnl_client is not None
    assert hasattr(pnl_client, "get_parser")
    assert hasattr(pnl_client, "extract_pnl_table")
    assert hasattr(pnl_client, "extract_all_pnl_tables")


@pytest.mark.asyncio
async def test_pnl_client_parser_caching(pnl_client):
    """Test parser caching functionality."""
    # Get parser for same table twice
    parser1 = pnl_client.get_parser("costs")
    parser2 = pnl_client.get_parser("costs")

    # Should return the same cached instance
    assert parser1 is parser2

    # Different tables should have different parsers
    parser3 = pnl_client.get_parser("quotes")
    assert parser1 is not parser3


@pytest.mark.asyncio
async def test_extract_pnl_table_costs(pnl_client):
    """Test extracting the critical costs table with pagination detection."""
    df = await pnl_client.extract_pnl_table(
        TEST_SPREADSHEET_ID, "costs", engine="polars"
    )

    assert isinstance(df, pl.DataFrame)
    assert (
        len(df) > 100
    ), f"Costs table should have substantial data, got {len(df)} rows"
    assert (
        len(df.columns) >= 5
    ), f"Costs should have multiple columns, got {len(df.columns)}"

    # Check for expected columns (allowing for transformations)
    expected_cols = ["Date", "Account", "gen_proj", "Debit", "Credit"]
    found_cols = [col for col in expected_cols if col in df.columns]
    assert len(found_cols) >= 3, f"Should find key columns, found: {found_cols}"

    # Critical: check if we're getting full data or just paginated subset
    if len(df) < 5000:
        import warnings

        warnings.warn(
            f"Costs table has only {len(df)} rows, expected >5k. "
            "This may indicate a pagination issue.",
            UserWarning,
        )


@pytest.mark.asyncio
async def test_extract_pnl_table_report_scope_projects(pnl_client):
    """Test extracting report_scope_projects with offset headers."""
    df = await pnl_client.extract_pnl_table(
        TEST_SPREADSHEET_ID, "report_scope_projects", engine="polars"
    )

    assert isinstance(df, pl.DataFrame)
    assert (
        len(df) > 100
    ), f"Scope projects should have substantial data, got {len(df)} rows"
    assert (
        len(df.columns) >= 50
    ), f"Scope projects should have many columns, got {len(df.columns)}"

    # Check for expected columns (from TODO requirements)
    expected_cols = ["name", "jan_24", "feb_24", "mar_24", "apr_24"]
    found_cols = [col for col in expected_cols if col in df.columns]
    assert len(found_cols) >= 3, f"Should find expected columns, found: {found_cols}"


@pytest.mark.asyncio
async def test_extract_pnl_table_both_engines(pnl_client):
    """Test both Polars and Pandas engines produce consistent results."""
    table_name = "quotes"

    # Extract with both engines
    df_polars = await pnl_client.extract_pnl_table(
        TEST_SPREADSHEET_ID, table_name, engine="polars"
    )
    df_pandas = await pnl_client.extract_pnl_table(
        TEST_SPREADSHEET_ID, table_name, engine="pandas"
    )

    # Verify types
    assert isinstance(df_polars, pl.DataFrame)
    assert isinstance(df_pandas, pd.DataFrame)

    # Verify consistency
    assert df_polars.shape == df_pandas.shape, "Shapes should match between engines"

    polars_cols = set(df_polars.columns)
    pandas_cols = set(df_pandas.columns)
    assert polars_cols == pandas_cols, "Column names should match between engines"


@pytest.mark.asyncio
async def test_extract_all_pnl_tables(pnl_client):
    """Test extracting multiple P&L tables efficiently."""
    # Test subset of tables to avoid long test times
    test_tables = ["costs", "quotes", "xero_name"]

    results = await pnl_client.extract_all_pnl_tables(
        TEST_SPREADSHEET_ID, tables=test_tables, engine="polars"
    )

    assert len(results) == len(test_tables)

    for table_name in test_tables:
        assert table_name in results
        df = results[table_name]
        assert isinstance(df, pl.DataFrame)
        assert len(df) > 0, f"Table {table_name} should have data"
        assert len(df.columns) > 0, f"Table {table_name} should have columns"


@pytest.mark.asyncio
async def test_extract_pnl_constants_tables(pnl_client):
    """Test extracting multiple tables from constants sheet."""
    constants_tables = await pnl_client.extract_pnl_constants_tables(
        TEST_SPREADSHEET_ID, engine="polars"
    )

    # Should find at least some constants tables
    assert len(constants_tables) >= 1, "Should extract at least one constants table"

    for table_name, df in constants_tables.items():
        assert isinstance(df, pl.DataFrame)
        assert len(df) > 0, f"Constants table {table_name} should have data"
        assert len(df.columns) > 0, f"Constants table {table_name} should have columns"


@pytest.mark.asyncio
async def test_validate_pnl_extraction(pnl_client):
    """Test P&L table validation without full data download."""
    # Test subset for performance
    test_tables = ["costs", "quotes", "report_scope_projects"]

    validation_results = await pnl_client.validate_pnl_extraction(
        TEST_SPREADSHEET_ID, tables=test_tables
    )

    assert len(validation_results) == len(test_tables)

    for table_name in test_tables:
        assert table_name in validation_results
        result = validation_results[table_name]

        assert "table_exists" in result
        assert "validation_passed" in result
        assert "parser_type" in result

        if result["table_exists"]:
            assert result["sample_row_count"] > 0
            assert "sample_headers" in result


@pytest.mark.asyncio
async def test_parsed_table_metadata(pnl_client):
    """Test that parsed tables include proper metadata."""
    parsed_table = await pnl_client.get_sheet_as_parsed_table(
        TEST_SPREADSHEET_ID, "costs"
    )

    assert parsed_table.name == "costs"
    assert parsed_table.row_count > 0
    assert parsed_table.column_count > 0
    assert parsed_table.parser_used in ["standard_paginated", "paginated"]

    # Check metadata structure
    assert "validation_passed" in parsed_table.metadata
    assert "header_row" in parsed_table.metadata
    assert "original_row_count" in parsed_table.metadata

    # For costs table specifically, check pagination metadata
    if parsed_table.parser_used == "standard_paginated":
        assert "likely_paginated" in parsed_table.metadata
        assert "pagination_size" in parsed_table.metadata


@pytest.mark.asyncio
async def test_error_handling_invalid_table(pnl_client):
    """Test error handling for invalid table names."""
    with pytest.raises(ValueError, match="Unknown P&L table"):
        await pnl_client.extract_pnl_table(TEST_SPREADSHEET_ID, "nonexistent_table")


@pytest.mark.asyncio
async def test_error_handling_invalid_spreadsheet(pnl_client):
    """Test error handling for invalid spreadsheet ID."""
    with pytest.raises(Exception):  # Should raise some API-related exception
        await pnl_client.extract_pnl_table("invalid_spreadsheet_id", "costs")


# ===== PERFORMANCE AND INTEGRATION TESTS =====


@pytest.mark.asyncio
async def test_pnl_extraction_performance(pnl_client):
    """Test P&L extraction performance with timing."""
    import time

    # Test a medium-sized table
    start_time = time.time()
    df = await pnl_client.extract_pnl_table(
        TEST_SPREADSHEET_ID, "quotes", engine="polars"
    )
    extraction_time = time.time() - start_time

    # Performance assertions
    assert (
        extraction_time < 30
    ), f"Extraction should complete in <30s, took {extraction_time:.2f}s"
    assert len(df) > 100, f"Should extract substantial data, got {len(df)} rows"

    print(
        f"✅ Extracted {len(df)} rows × {len(df.columns)} columns in {extraction_time:.2f}s"
    )


@pytest.mark.asyncio
async def test_comprehensive_pnl_validation():
    """Comprehensive test of all P&L table configurations."""
    # Validate all table configurations
    for table_name in REQUIRED_PNL_TABLES:
        config = PNL_PARSER_CONFIGS[table_name]
        parser_type = PNL_PARSER_TYPES[table_name]

        # Test parser creation
        parser = create_pnl_parser(table_name)
        assert parser is not None

        # Validate configuration consistency
        assert config.header_row >= 1
        assert config.expected_min_rows > 0

        if parser_type == "offset_header":
            # Specific validation for offset header tables
            assert not config.auto_detect_headers or config.header_row > 1
        elif parser_type == "multi_table":
            # Specific validation for multi-table sheets
            assert config.max_blank_rows >= 3
        elif parser_type == "standard_paginated":
            # Specific validation for paginated tables
            assert config.pagination_size > 0

        print(
            f"✅ Validated {table_name}: {parser_type} parser with {config.expected_min_rows} min rows"
        )


if __name__ == "__main__":
    # Run specific test for debugging
    import asyncio

    async def debug_test():
        client = PnLGoogleSheetsClient()
        validation = await test_validate_pnl_extraction(client)
        print("Validation completed:", validation)

    asyncio.run(debug_test())
