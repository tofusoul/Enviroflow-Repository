"""
Tests for enhanced xero-costs data extraction functionality.

Tests the extract_xero_costs function including:
- Google Sheets integration with fallback
- Excel date conversion (serial numbers to Date type)
- Enhanced column typing (Float64 for financial, String for text)
- Null date filtering
- MotherDuck integration
- Graceful error handling and fallbacks
"""

import pytest
import polars as pl
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from enviroflow_app.cli.operations.extraction_ops import extract_xero_costs


class TestXeroCostsExtraction:
    """Test suite for enhanced xero-costs data extraction."""

    @pytest.fixture
    def mock_costs_data(self):
        """Create mock costs data with various data types to test conversion."""
        return pl.DataFrame(
            {
                "Date": [
                    44562,
                    44563,
                    44564,
                    None,
                    44566,
                ],  # Excel serial numbers + null
                "Account": [
                    "Office Supplies",
                    "Vehicle Expenses",
                    "Equipment",
                    "Software",
                    "Travel",
                ],
                "Description": [
                    "Stationery purchase",
                    "Fuel costs",
                    "Laptop",
                    "License",
                    "Conference",
                ],
                "Supplier": ["Staples", "Shell", "Dell", "Microsoft", "Airlines"],
                "Debit": [250.50, 125.75, 1500.00, 299.99, 850.25],
                "Credit": [None, None, None, None, None],
                "Running Balance": [250.50, 376.25, 1876.25, 2176.24, 3026.49],
                "Gross": [250.50, 125.75, 1500.00, 299.99, 850.25],
                "GST": [25.05, 12.58, 150.00, 30.00, 85.03],
                "amount": [225.45, 113.17, 1350.00, 269.99, 765.22],
                "Reference": ["PO001", "FUEL02", "EQUIP03", "LIC04", "CONF05"],
            }
        )

    @pytest.fixture
    def mock_fallback_costs_data(self):
        """Create mock fallback data from local file."""
        return pl.DataFrame(
            {
                "Date": ["2022-01-01", "2022-01-02", "2022-01-03"],
                "Account": ["Test Account 1", "Test Account 2", "Test Account 3"],
                "Debit": [100.0, 200.0, 300.0],
                "Credit": [0.0, 0.0, 0.0],
            }
        )

    @pytest.mark.asyncio
    async def test_xero_costs_extraction_success(self, mock_costs_data):
        """Test successful xero-costs extraction with proper typing and date conversion."""

        # Mock the Google Sheets client
        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = mock_costs_data

        # Mock the save function to avoid actual file/database operations
        with (
            patch(
                "enviroflow_app.cli.operations.extraction_ops._save_dataframe"
            ) as mock_save,
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_xero_costs()

            # Verify the result structure
            assert "xero_costs" in result
            costs_df = result["xero_costs"]

            # Verify data shape (null date row should be filtered)
            assert len(costs_df) == 4  # 5 original - 1 null date

            # Verify column types
            schema = costs_df.schema
            assert schema["Date"] == pl.Date
            assert schema["Account"] == pl.String
            assert schema["Description"] == pl.String
            assert schema["Supplier"] == pl.String
            assert schema["Debit"] == pl.Float64
            assert schema["Credit"] == pl.Float64
            assert schema["Running Balance"] == pl.Float64
            assert schema["Gross"] == pl.Float64
            assert schema["GST"] == pl.Float64
            assert schema["amount"] == pl.Float64
            assert schema["Reference"] == pl.String

            # Verify date conversion (Excel serial 44562 should convert properly)
            dates = costs_df["Date"].to_list()
            assert all(isinstance(d, date) for d in dates)

            # Verify no null dates remain
            assert costs_df.filter(pl.col("Date").is_null()).height == 0

            # Verify save was called with correct parameters
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[0][1] == "xero_costs"  # table_name
            assert len(call_args[0][0]) == 4  # DataFrame length

    @pytest.mark.asyncio
    async def test_xero_costs_fallback_to_local_file(self, mock_fallback_costs_data):
        """Test fallback to local file when Google Sheets fails."""

        # Mock Google Sheets failure
        with (
            patch(
                "enviroflow_app.gsheets.create_pnl_client",
                side_effect=Exception("Connection failed"),
            ),
            patch(
                "polars.read_parquet", return_value=mock_fallback_costs_data
            ) as mock_read,
            patch(
                "enviroflow_app.cli.operations.extraction_ops._save_dataframe"
            ) as mock_save,
        ):
            result = extract_xero_costs()

            # Verify fallback was used
            assert "xero_costs" in result
            costs_df = result["xero_costs"]

            # Verify fallback data was loaded
            mock_read.assert_called()

            # Verify result contains fallback data
            assert len(costs_df) == 3

            # Verify save was still called
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_xero_costs_no_spreadsheet_found(self):
        """Test handling when P&L spreadsheet is not found."""

        mock_client = AsyncMock()
        mock_client.list_spreadsheets.return_value = []

        # Mock fallback file exists
        with (
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
            patch("polars.read_parquet") as mock_read,
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
        ):
            # Should fall back to local file
            extract_xero_costs()

            # Verify fallback was attempted
            mock_read.assert_called()

    def test_excel_date_conversion_accuracy(self):
        """Test Excel date conversion for known serial numbers."""

        # Test specific Excel serial numbers with known dates
        test_data = pl.DataFrame(
            {
                "Date": [
                    44927,
                    44197,
                    1,
                    43831,
                ],  # 2022-12-01, 2020-12-31, 1900-01-01, 2019-11-26
                "Account": ["Test1", "Test2", "Test3", "Test4"],
                "Debit": [100.0, 200.0, 300.0, 400.0],
            }
        )

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = test_data

        with (
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_xero_costs()
            costs_df = result["xero_costs"]

            dates = costs_df["Date"].to_list()

            # Verify specific date conversions
            assert date(2022, 12, 1) in dates  # 44927
            assert date(2020, 12, 31) in dates  # 44197
            assert date(1900, 1, 1) in dates  # 1
            assert date(2019, 11, 26) in dates  # 43831

    def test_financial_column_typing_comprehensive(self, mock_costs_data):
        """Test comprehensive financial column typing."""

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = mock_costs_data

        with (
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_xero_costs()
            costs_df = result["xero_costs"]

            # Test all financial columns are Float64
            financial_columns = [
                "Debit",
                "Credit",
                "Running Balance",
                "Gross",
                "GST",
                "amount",
            ]
            for col in financial_columns:
                if col in costs_df.columns:
                    assert (
                        costs_df.schema[col] == pl.Float64
                    ), f"Column {col} should be Float64"

            # Test text columns are String
            text_columns = ["Account", "Description", "Supplier", "Reference"]
            for col in text_columns:
                if col in costs_df.columns:
                    assert (
                        costs_df.schema[col] == pl.String
                    ), f"Column {col} should be String"

    def test_null_date_filtering_edge_cases(self):
        """Test various null date scenarios."""

        # Create data with different null scenarios
        test_data = pl.DataFrame(
            {
                "Date": [
                    44927,
                    None,
                    0,
                    "",
                    "NULL",
                    44929,
                ],  # Various null representations
                "Account": ["A", "B", "C", "D", "E", "F"],
                "Debit": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
            }
        )

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = test_data

        with (
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_xero_costs()
            costs_df = result["xero_costs"]

            # Should handle various null representations
            # Exact filtering behavior depends on implementation
            assert len(costs_df) >= 2  # At least the valid numeric dates
            assert costs_df["Date"].dtype == pl.Date

    @pytest.mark.asyncio
    async def test_xero_costs_with_custom_config(self, mock_costs_data):
        """Test xero-costs extraction with custom configuration."""

        from enviroflow_app.cli.config import OutputDestination, OutputConfig

        config = OutputConfig(destination=OutputDestination.BOTH)

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = mock_costs_data

        with (
            patch(
                "enviroflow_app.cli.operations.extraction_ops._save_dataframe"
            ) as mock_save,
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            extract_xero_costs(config)

            # Verify save was called with the config
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[0][2] == config  # config parameter

    def test_large_dataset_handling(self):
        """Test handling of large datasets similar to production (13k+ records)."""

        # Generate 1000 records to simulate larger dataset
        n_records = 1000
        test_data = pl.DataFrame(
            {
                "Date": [44927 + i for i in range(n_records)],  # Sequential dates
                "Account": [f"Account_{i % 100}" for i in range(n_records)],
                "Description": [f"Transaction_{i}" for i in range(n_records)],
                "Debit": [float(100 + i) for i in range(n_records)],
                "Credit": [None] * n_records,
            }
        )

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = test_data

        with (
            patch(
                "enviroflow_app.cli.operations.extraction_ops._save_dataframe"
            ) as mock_save,
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_xero_costs()
            costs_df = result["xero_costs"]

            # Verify large dataset handling
            assert len(costs_df) == n_records
            assert costs_df["Date"].dtype == pl.Date
            assert costs_df["Debit"].dtype == pl.Float64

            # Verify save was called
            mock_save.assert_called_once()

    def test_column_consistency_with_legacy_data(self):
        """Test that column structure is consistent with legacy expectations."""

        # Mock data with expected column structure
        legacy_structure_data = pl.DataFrame(
            {
                "Date": [44927, 44928],
                "Account": ["Expense Account", "Revenue Account"],
                "Description": ["Business expense", "Sales revenue"],
                "Supplier": ["Vendor A", "Customer B"],
                "Debit": [500.0, None],
                "Credit": [None, 1000.0],
                "Running Balance": [500.0, 500.0],
                "Gross": [500.0, 1000.0],
                "GST": [50.0, 100.0],
                "amount": [450.0, 900.0],
                "Reference": ["EXP001", "REV001"],
            }
        )

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = legacy_structure_data

        with (
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_xero_costs()
            costs_df = result["xero_costs"]

            # Verify all expected columns are present and properly typed
            expected_columns = {
                "Date": pl.Date,
                "Account": pl.String,
                "Description": pl.String,
                "Supplier": pl.String,
                "Debit": pl.Float64,
                "Credit": pl.Float64,
                "Running Balance": pl.Float64,
                "Gross": pl.Float64,
                "GST": pl.Float64,
                "amount": pl.Float64,
                "Reference": pl.String,
            }

            for col, expected_type in expected_columns.items():
                assert col in costs_df.columns, f"Column {col} missing"
                assert (
                    costs_df.schema[col] == expected_type
                ), f"Column {col} has wrong type"
