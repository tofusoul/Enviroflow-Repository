"""
Tests for sales data extraction functionality.

Tests the extract_sales_data function including:
- Google Sheets integration
- Excel date conversion
- Column typing (Date, Float64, String)
- Null date filtering
- MotherDuck integration
- Data quality validation
"""

import pytest
import polars as pl
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from enviroflow_app.cli.operations.extraction_ops import extract_sales_data


class TestSalesExtraction:
    """Test suite for sales data extraction."""

    @pytest.fixture
    def mock_sales_data(self):
        """Create mock sales data with various data types to test conversion."""
        return pl.DataFrame(
            {
                "Date": [
                    "44927",
                    "44928",
                    "44929",
                    None,
                    "44931",
                ],  # Excel serial numbers as strings + null
                "Account": [
                    "Sales Revenue",
                    "Service Income",
                    "Product Sales",
                    "Refunds",
                    "Consulting",
                ],
                "Description": [
                    "Product A Sale",
                    "Service B",
                    "Product C",
                    "Return",
                    "Project X",
                ],
                "Supplier": [
                    "Customer 1",
                    "Customer 2",
                    "Customer 3",
                    "Customer 1",
                    "Customer 4",
                ],
                "Debit": [None, "1500.50", None, "250.00", None],
                "Credit": ["1000.00", None, "2500.75", None, "750.25"],
                "Running Balance": [
                    "1000.00",
                    "-500.50",
                    "2000.25",
                    "1750.25",
                    "2500.50",
                ],
                "Gross": ["1000.00", "1500.50", "2500.75", "-250.00", "750.25"],
                "GST": ["100.00", "150.05", "250.08", "-25.00", "75.03"],
                "amount": ["900.00", "1350.45", "2250.67", "-225.00", "675.22"],
                "Reference": ["INV001", "SRV002", "PRD003", "REF001", "CON004"],
            }
        )

    @pytest.fixture
    def expected_typed_data(self):
        """Expected data after proper typing and null filtering."""
        return pl.DataFrame(
            {
                "Date": [
                    date(2022, 12, 1),
                    date(2022, 12, 2),
                    date(2022, 12, 3),
                    date(2022, 12, 5),
                ],
                "Account": [
                    "Sales Revenue",
                    "Service Income",
                    "Product Sales",
                    "Consulting",
                ],
                "Description": [
                    "Product A Sale",
                    "Service B",
                    "Product C",
                    "Project X",
                ],
                "Supplier": ["Customer 1", "Customer 2", "Customer 3", "Customer 4"],
                "Debit": [None, 1500.50, None, None],
                "Credit": [1000.00, None, 2500.75, 750.25],
                "Running Balance": [1000.00, -500.50, 2000.25, 2500.50],
                "Gross": [1000.00, 1500.50, 2500.75, 750.25],
                "GST": [100.00, 150.05, 250.08, 75.03],
                "amount": [900.00, 1350.45, 2250.67, 675.22],
                "Reference": ["INV001", "SRV002", "PRD003", "CON004"],
            }
        )

    @pytest.mark.asyncio
    async def test_sales_extraction_success(self, mock_sales_data):
        """Test successful sales data extraction with proper typing."""

        # Mock the Google Sheets client
        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = mock_sales_data

        # Mock the save function to avoid actual file/database operations
        with (
            patch(
                "enviroflow_app.cli.operations.extraction_ops._save_dataframe"
            ) as mock_save,
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_sales_data()

            # Verify the result structure
            assert "sales_data" in result
            sales_df = result["sales_data"]

            # Verify data shape (null date row should be filtered)
            assert len(sales_df) == 4  # 5 original - 1 null date

            # Verify column types
            schema = sales_df.schema
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

            # Verify date conversion (Excel serial 44927 = 2022-12-01)
            dates = sales_df["Date"].to_list()
            assert date(2022, 12, 1) in dates
            assert date(2022, 12, 2) in dates

            # Verify no null dates remain
            assert sales_df.filter(pl.col("Date").is_null()).height == 0

            # Verify save was called with correct parameters
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[0][1] == "xero_sales"  # table_name
            assert len(call_args[0][0]) == 4  # DataFrame length

    @pytest.mark.asyncio
    async def test_sales_extraction_no_spreadsheet_found(self):
        """Test handling when P&L spreadsheet is not found."""

        mock_client = AsyncMock()
        mock_client.list_spreadsheets.return_value = []

        with patch(
            "enviroflow_app.gsheets.create_pnl_client", return_value=mock_client
        ):
            with pytest.raises(
                ValueError, match="Project P&L Report spreadsheet not found"
            ):
                extract_sales_data()

    @pytest.mark.asyncio
    async def test_sales_extraction_google_sheets_failure(self):
        """Test fallback behavior when Google Sheets extraction fails."""

        with patch(
            "enviroflow_app.gsheets.create_pnl_client",
            side_effect=Exception("Connection failed"),
        ):
            # Should raise exception since no fallback for sales data
            with pytest.raises(Exception):
                extract_sales_data()

    def test_date_conversion_edge_cases(self):
        """Test Excel date conversion edge cases."""
        from enviroflow_app.cli.operations.extraction_ops import extract_sales_data

        # Test data with edge case dates
        edge_case_data = pl.DataFrame(
            {
                "Date": [1, 44197, 0, None],  # Very early date, recent date, zero, null
                "Account": ["Test1", "Test2", "Test3", "Test4"],
                "Debit": [100.0, 200.0, 300.0, 400.0],
            }
        )

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = edge_case_data

        with (
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_sales_data()
            sales_df = result["sales_data"]

            # Should handle edge cases gracefully
            # Date 1 = 1900-01-01, Date 44197 = 2020-12-31, Date 0 should be handled
            assert len(sales_df) >= 2  # At least non-null dates
            assert sales_df["Date"].dtype == pl.Date

    def test_financial_column_typing(self, mock_sales_data):
        """Test that all financial columns are properly typed as Float64."""

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = mock_sales_data

        with (
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_sales_data()
            sales_df = result["sales_data"]

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
                if col in sales_df.columns:
                    assert (
                        sales_df.schema[col] == pl.Float64
                    ), f"Column {col} should be Float64"

    def test_string_column_typing(self, mock_sales_data):
        """Test that text columns are properly typed as String."""

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = mock_sales_data

        with (
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_sales_data()
            sales_df = result["sales_data"]

            # Test text columns are String
            text_columns = ["Account", "Description", "Supplier", "Reference"]
            for col in text_columns:
                if col in sales_df.columns:
                    assert (
                        sales_df.schema[col] == pl.String
                    ), f"Column {col} should be String"

    @pytest.mark.asyncio
    async def test_sales_extraction_with_config(self, mock_sales_data):
        """Test sales extraction with custom configuration."""

        from enviroflow_app.cli.config import OutputDestination, OutputConfig

        config = OutputConfig(destination=OutputDestination.LOCAL)

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = mock_sales_data

        with (
            patch(
                "enviroflow_app.cli.operations.extraction_ops._save_dataframe"
            ) as mock_save,
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            extract_sales_data(config)

            # Verify save was called with the config
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[0][2] == config  # config parameter

    def test_null_date_filtering_comprehensive(self):
        """Test comprehensive null date filtering scenarios."""

        # Create data with various null scenarios
        test_data = pl.DataFrame(
            {
                "Date": [44927, None, 44929, 0, None, 44931],
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
            result = extract_sales_data()
            sales_df = result["sales_data"]

            # Should filter out the 2 null dates but keep the 0 (1899-12-30)
            expected_length = 4  # 6 original - 2 nulls
            assert len(sales_df) == expected_length

            # Verify no nulls remain
            assert sales_df.filter(pl.col("Date").is_null()).height == 0
