"""
Integration tests for enhanced extraction pipeline.

Tests end-to-end extraction functionality including:
- MotherDuck integration and saving
- Column typing across all extract operations
- Full pipeline execution with enhanced data processing
- Real-world data volume handling
- Error recovery and fallback scenarios
"""

import pytest
import polars as pl
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from enviroflow_app.cli.operations.extraction_ops import (
    extract_xero_costs,
    extract_sales_data,
)
from enviroflow_app.cli.config import OutputDestination, OutputConfig, PipelineConfig


class TestEnhancedExtractionIntegration:
    """Integration tests for enhanced extraction pipeline."""

    @pytest.fixture
    def mock_motherduck_connection(self):
        """Mock MotherDuck connection for testing."""
        mock_md = MagicMock()
        mock_md.save_dataframe = MagicMock()
        return mock_md

    @pytest.fixture
    def large_xero_costs_data(self):
        """Create large xero costs dataset similar to production."""
        n_records = 1000  # Simulate subset of 13,652 production records
        return pl.DataFrame(
            {
                "Date": [44927 + i for i in range(n_records)],  # Sequential Excel dates
                "Account": [f"Account_{i % 50}" for i in range(n_records)],
                "Description": [f"Transaction_{i}" for i in range(n_records)],
                "Supplier": [f"Supplier_{i % 100}" for i in range(n_records)],
                "Debit": [
                    100.0 + (i * 1.5) if i % 3 == 0 else None for i in range(n_records)
                ],
                "Credit": [
                    200.0 + (i * 2.0) if i % 3 != 0 else None for i in range(n_records)
                ],
                "Running Balance": [1000.0 + (i * 10.0) for i in range(n_records)],
                "Gross": [100.0 + (i * 1.2) for i in range(n_records)],
                "GST": [10.0 + (i * 0.12) for i in range(n_records)],
                "amount": [90.0 + (i * 1.08) for i in range(n_records)],
                "Reference": [f"REF_{i:06d}" for i in range(n_records)],
            }
        )

    @pytest.fixture
    def large_sales_data(self):
        """Create large sales dataset similar to production."""
        n_records = 1500  # Simulate subset of 30,996 production records
        return pl.DataFrame(
            {
                "Date": [44927 + i for i in range(n_records)],  # Sequential Excel dates
                "Account": [f"Sales_{i % 25}" for i in range(n_records)],
                "Description": [f"Sale_{i}" for i in range(n_records)],
                "Supplier": [f"Customer_{i % 75}" for i in range(n_records)],
                "Debit": [
                    None if i % 2 == 0 else 150.0 + (i * 0.5) for i in range(n_records)
                ],
                "Credit": [
                    300.0 + (i * 1.8) if i % 2 == 0 else None for i in range(n_records)
                ],
                "Running Balance": [5000.0 + (i * 15.0) for i in range(n_records)],
                "Gross": [280.0 + (i * 1.6) for i in range(n_records)],
                "GST": [28.0 + (i * 0.16) for i in range(n_records)],
                "amount": [252.0 + (i * 1.44) for i in range(n_records)],
                "Reference": [f"SALE_{i:06d}" for i in range(n_records)],
            }
        )

    @pytest.mark.asyncio
    async def test_xero_costs_motherduck_integration(
        self, large_xero_costs_data, mock_motherduck_connection
    ):
        """Test xero-costs extraction with MotherDuck integration."""

        # Mock Google Sheets client
        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = large_xero_costs_data

        # Mock MotherDuck connection
        with (
            patch("enviroflow_app.elt.motherduck.md", mock_motherduck_connection),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            # Test with MotherDuck configuration
            config = OutputConfig(destination=OutputDestination.MOTHERDUCK)
            result = extract_xero_costs(config)

            # Verify extraction success
            assert "xero_costs" in result
            costs_df = result["xero_costs"]

            # Verify data volume
            assert len(costs_df) == 1000

            # Verify column typing
            assert costs_df.schema["Date"] == pl.Date
            assert costs_df.schema["Debit"] == pl.Float64
            assert costs_df.schema["Credit"] == pl.Float64
            assert costs_df.schema["Account"] == pl.String

            # Verify MotherDuck save was called
            mock_motherduck_connection.save_dataframe.assert_called_once()
            call_args = mock_motherduck_connection.save_dataframe.call_args
            assert call_args[0][1] == "xero_costs"  # table name

    @pytest.mark.asyncio
    async def test_sales_motherduck_integration(
        self, large_sales_data, mock_motherduck_connection
    ):
        """Test sales extraction with MotherDuck integration."""

        # Mock Google Sheets client
        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = large_sales_data

        # Mock MotherDuck connection
        with (
            patch("enviroflow_app.elt.motherduck.md", mock_motherduck_connection),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            # Test with MotherDuck configuration
            config = OutputConfig(destination=OutputDestination.MOTHERDUCK)
            result = extract_sales_data(config)

            # Verify extraction success
            assert "sales_data" in result
            sales_df = result["sales_data"]

            # Verify data volume
            assert len(sales_df) == 1500

            # Verify comprehensive column typing
            assert sales_df.schema["Date"] == pl.Date
            assert sales_df.schema["Debit"] == pl.Float64
            assert sales_df.schema["Credit"] == pl.Float64
            assert sales_df.schema["Running Balance"] == pl.Float64
            assert sales_df.schema["Gross"] == pl.Float64
            assert sales_df.schema["GST"] == pl.Float64
            assert sales_df.schema["amount"] == pl.Float64
            assert sales_df.schema["Account"] == pl.String
            assert sales_df.schema["Description"] == pl.String

            # Verify MotherDuck save was called
            mock_motherduck_connection.save_dataframe.assert_called_once()
            call_args = mock_motherduck_connection.save_dataframe.call_args
            assert call_args[0][1] == "xero_sales"  # table name

    @pytest.mark.asyncio
    async def test_dual_output_configuration(
        self, large_xero_costs_data, mock_motherduck_connection
    ):
        """Test extraction with both local and MotherDuck output."""

        # Mock Google Sheets client
        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = large_xero_costs_data

        # Create output directories for testing
        test_output_dir = Path("test_output")
        test_output_dir.mkdir(exist_ok=True)

        try:
            with (
                patch("enviroflow_app.elt.motherduck.md", mock_motherduck_connection),
                patch(
                    "enviroflow_app.gsheets.create_pnl_client", return_value=mock_client
                ),
                patch(
                    "enviroflow_app.cli.operations.extraction_ops.PROCESSED_PARQUET_DIR",
                    test_output_dir,
                ),
            ):
                # Test with BOTH configuration
                config = OutputConfig(
                    destination=OutputDestination.BOTH, local_dir=test_output_dir
                )
                result = extract_xero_costs(config)

                # Verify extraction success
                assert "xero_costs" in result
                costs_df = result["xero_costs"]
                assert len(costs_df) == 1000

                # Verify MotherDuck save was called
                mock_motherduck_connection.save_dataframe.assert_called_once()

                # Verify local file would be created (mocked directory)
                assert test_output_dir.exists()

        finally:
            # Cleanup
            if test_output_dir.exists():
                import shutil

                shutil.rmtree(test_output_dir)

    def test_date_conversion_accuracy_integration(self):
        """Test accurate date conversion across different scenarios."""

        # Test data with known Excel serial numbers
        test_data = pl.DataFrame(
            {
                "Date": [
                    44927,  # 2022-12-01
                    44197,  # 2020-12-31
                    43831,  # 2019-11-26
                    45291,  # 2023-11-29
                    1,  # 1900-01-01
                ],
                "Account": ["Test1", "Test2", "Test3", "Test4", "Test5"],
                "Debit": [100.0, 200.0, 300.0, 400.0, 500.0],
            }
        )

        expected_dates = [
            date(2022, 12, 1),
            date(2020, 12, 31),
            date(2019, 11, 26),
            date(2023, 11, 29),
            date(1900, 1, 1),
        ]

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

            # Verify all dates converted correctly
            actual_dates = costs_df["Date"].to_list()
            for expected_date in expected_dates:
                assert expected_date in actual_dates

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, mock_motherduck_connection):
        """Test error recovery and fallback scenarios."""

        # Test Google Sheets failure with fallback
        fallback_data = pl.DataFrame(
            {
                "Date": ["2022-01-01", "2022-01-02"],
                "Account": ["Fallback 1", "Fallback 2"],
                "Debit": [100.0, 200.0],
            }
        )

        with (
            patch(
                "enviroflow_app.gsheets.create_pnl_client",
                side_effect=Exception("Connection failed"),
            ),
            patch("polars.read_parquet", return_value=fallback_data),
            patch("enviroflow_app.elt.motherduck.md", mock_motherduck_connection),
        ):
            result = extract_xero_costs()

            # Verify fallback worked
            assert "xero_costs" in result
            costs_df = result["xero_costs"]
            assert len(costs_df) == 2

            # Verify MotherDuck save was still attempted
            mock_motherduck_connection.save_dataframe.assert_called_once()

    def test_data_quality_validation_integration(self):
        """Test comprehensive data quality validation."""

        # Create data with quality issues
        problematic_data = pl.DataFrame(
            {
                "Date": [44927, None, 44929, "", "invalid", 44931, 0],
                "Account": ["Valid1", None, "Valid3", "", "Valid5", "Valid6", "Valid7"],
                "Debit": [100.0, "invalid", 300.0, None, 500.0, 600.0, 700.0],
                "Credit": [None, 200.0, None, 400.0, None, None, 800.0],
            }
        )

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = problematic_data

        with (
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            result = extract_xero_costs()
            costs_df = result["xero_costs"]

            # Verify data quality improvements
            # Should filter out rows with null dates
            assert all(costs_df["Date"].is_not_null())

            # Verify proper typing was applied
            assert costs_df.schema["Date"] == pl.Date
            assert costs_df.schema["Debit"] == pl.Float64
            assert costs_df.schema["Credit"] == pl.Float64

    @pytest.mark.asyncio
    async def test_pipeline_config_integration(
        self, large_xero_costs_data, mock_motherduck_connection
    ):
        """Test integration with PipelineConfig."""

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]
        mock_client.extract_pnl_table.return_value = large_xero_costs_data

        with (
            patch("enviroflow_app.elt.motherduck.md", mock_motherduck_connection),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            # Create pipeline configuration
            pipeline_config = PipelineConfig.create(
                destination=OutputDestination.MOTHERDUCK
            )

            result = extract_xero_costs(pipeline_config)

            # Verify extraction worked with pipeline config
            assert "xero_costs" in result
            costs_df = result["xero_costs"]
            assert len(costs_df) == 1000

            # Verify MotherDuck integration
            mock_motherduck_connection.save_dataframe.assert_called_once()

    def test_column_consistency_across_extractions(self):
        """Test that column structures are consistent across xero-costs and sales."""

        # Common financial columns that should be in both datasets
        expected_financial_columns = [
            "Debit",
            "Credit",
            "Running Balance",
            "Gross",
            "GST",
            "amount",
        ]
        expected_text_columns = ["Account", "Description", "Reference"]

        xero_data = pl.DataFrame(
            {
                "Date": [44927, 44928],
                **{col: [100.0, 200.0] for col in expected_financial_columns},
                **{
                    col: [f"Test_{col}", f"Test2_{col}"]
                    for col in expected_text_columns
                },
                "Supplier": ["Supplier1", "Supplier2"],
            }
        )

        sales_data = pl.DataFrame(
            {
                "Date": [44927, 44928],
                **{col: [300.0, 400.0] for col in expected_financial_columns},
                **{
                    col: [f"Sales_{col}", f"Sales2_{col}"]
                    for col in expected_text_columns
                },
                "Supplier": ["Customer1", "Customer2"],
            }
        )

        mock_client = AsyncMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Project P&L Report"
        mock_spreadsheet.spreadsheet_id = "test_id"

        mock_client.list_spreadsheets.return_value = [mock_spreadsheet]

        with (
            patch("enviroflow_app.cli.operations.extraction_ops._save_dataframe"),
            patch("enviroflow_app.gsheets.create_pnl_client", return_value=mock_client),
        ):
            # Test xero-costs
            mock_client.extract_pnl_table.return_value = xero_data
            xero_result = extract_xero_costs()
            xero_df = xero_result["xero_costs"]

            # Test sales
            mock_client.extract_pnl_table.return_value = sales_data
            sales_result = extract_sales_data()
            sales_df = sales_result["sales_data"]

            # Verify consistent column typing across both extractions
            for col in expected_financial_columns:
                assert (
                    xero_df.schema[col] == pl.Float64
                ), f"Xero {col} should be Float64"
                assert (
                    sales_df.schema[col] == pl.Float64
                ), f"Sales {col} should be Float64"

            for col in expected_text_columns:
                assert xero_df.schema[col] == pl.String, f"Xero {col} should be String"
                assert (
                    sales_df.schema[col] == pl.String
                ), f"Sales {col} should be String"

            # Both should have Date type for Date column
            assert xero_df.schema["Date"] == pl.Date
            assert sales_df.schema["Date"] == pl.Date
