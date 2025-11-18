"""
Enhanced Google Sheets client with injectable parsing for P&L data extraction.

This module extends the base GoogleSheetsClient with specialized methods for
extracting P&L tables using different parsing strategies.
"""

import logging
from typing import Any, Dict, List, Optional, Union

import polars as pl
import pandas as pd

from .gsheets import GoogleSheetsClient as BaseGoogleSheetsClient
from .parsers import (
    ParsedTable,
    ParsingConfig,
    TableParser,
    ParserFactory,
    create_pnl_parser,
    PNL_PARSER_CONFIGS,
    PNL_PARSER_TYPES,
)

logger = logging.getLogger(__name__)


class PnLGoogleSheetsClient(BaseGoogleSheetsClient):
    """
    Enhanced Google Sheets client for P&L data extraction with injectable parsers.

    Extends the base client with specialized methods for handling different
    table structures found in P&L spreadsheets.
    """

    def __init__(self):
        super().__init__()
        self._parser_cache: Dict[str, TableParser] = {}

    def get_parser(
        self,
        table_name: str,
        parser_type: Optional[str] = None,
        config: Optional[ParsingConfig] = None,
    ) -> TableParser:
        """
        Get or create a parser for the specified table.

        Args:
            table_name: Name of the table
            parser_type: Type of parser to use (overrides default)
            config: Custom parsing configuration (overrides default)

        Returns:
            Configured parser instance
        """
        cache_key = f"{table_name}_{parser_type}_{id(config) if config else 'default'}"

        if cache_key not in self._parser_cache:
            if table_name in PNL_PARSER_CONFIGS and not parser_type and not config:
                # Use pre-configured P&L parser
                parser = create_pnl_parser(table_name)
            else:
                # Create custom parser
                if not parser_type:
                    parser_type = "standard"
                if not config:
                    config = ParsingConfig()
                parser = ParserFactory.create_parser(parser_type, config)

            self._parser_cache[cache_key] = parser

        return self._parser_cache[cache_key]

    async def get_sheet_as_parsed_table(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        parser_type: Optional[str] = None,
        config: Optional[ParsingConfig] = None,
        range_name: Optional[str] = None,
    ) -> ParsedTable:
        """
        Get sheet data as a parsed table with validation.

        Args:
            spreadsheet_id: The spreadsheet ID or URL
            sheet_name: Name of the sheet
            parser_type: Type of parser to use
            config: Custom parsing configuration
            range_name: Specific range to extract

        Returns:
            ParsedTable with data and metadata
        """
        # Get raw data
        raw_data = await self.get_sheet_data(spreadsheet_id, sheet_name, range_name)

        if not raw_data:
            raise ValueError(f"No data found in sheet {sheet_name}")

        # Get appropriate parser
        parser = self.get_parser(sheet_name, parser_type, config)

        # Parse the data
        parsed_table = parser.parse(raw_data, sheet_name)

        # Validate the result
        is_valid = parser.validate(parsed_table)
        parsed_table.metadata["validation_passed"] = is_valid

        if not is_valid:
            logger.warning(f"Table {sheet_name} failed validation checks")

        return parsed_table

    async def extract_pnl_table(
        self, spreadsheet_id: str, table_name: str, engine: str = "polars"
    ) -> Union[pl.DataFrame, pd.DataFrame]:
        """
        Extract a specific P&L table using pre-configured parsing.

        Args:
            spreadsheet_id: The P&L spreadsheet ID
            table_name: Name of the P&L table (e.g., 'costs', 'constants')
            engine: DataFrame engine ('polars' or 'pandas')

        Returns:
            DataFrame with the extracted table data
        """
        if table_name not in PNL_PARSER_CONFIGS:
            raise ValueError(
                f"Unknown P&L table: {table_name}. Available: {list(PNL_PARSER_CONFIGS.keys())}"
            )

        # Extract using specialized parser
        parsed_table = await self.get_sheet_as_parsed_table(spreadsheet_id, table_name)

        # Log extraction results
        logger.info(
            f"Extracted P&L table '{table_name}': {parsed_table.row_count} rows × "
            f"{parsed_table.column_count} columns using {parsed_table.parser_used} parser"
        )

        # Check for critical issues
        if table_name == "costs" and parsed_table.metadata.get(
            "likely_paginated", False
        ):
            logger.error(
                f"CRITICAL: Costs table appears paginated with only {parsed_table.row_count} rows. "
                "Expected ~13k records according to requirements."
            )

        # Convert to requested engine
        if engine.lower() == "pandas":
            if isinstance(parsed_table.data, pl.DataFrame):
                return parsed_table.data.to_pandas()
            return parsed_table.data
        else:
            if isinstance(parsed_table.data, pd.DataFrame):
                return pl.from_pandas(parsed_table.data)
            return parsed_table.data

    async def extract_all_pnl_tables(
        self,
        spreadsheet_id: str,
        tables: Optional[List[str]] = None,
        engine: str = "polars",
    ) -> Dict[str, Union[pl.DataFrame, pd.DataFrame]]:
        """
        Extract multiple P&L tables efficiently.

        Args:
            spreadsheet_id: The P&L spreadsheet ID
            tables: List of table names to extract (None = all configured tables)
            engine: DataFrame engine ('polars' or 'pandas')

        Returns:
            Dictionary mapping table names to DataFrames
        """
        if tables is None:
            tables = list(PNL_PARSER_CONFIGS.keys())

        results = {}
        extraction_stats = {
            "successful": 0,
            "failed": 0,
            "warnings": 0,
            "total_rows": 0,
        }

        logger.info(
            f"Extracting {len(tables)} P&L tables from spreadsheet {spreadsheet_id}"
        )

        for table_name in tables:
            try:
                logger.info(f"Extracting table: {table_name}")
                df = await self.extract_pnl_table(spreadsheet_id, table_name, engine)
                results[table_name] = df

                extraction_stats["successful"] += 1
                extraction_stats["total_rows"] += len(df)

                logger.info(
                    f"✅ {table_name}: {len(df)} rows × {len(df.columns)} columns"
                )

            except Exception as e:
                logger.error(f"❌ Failed to extract {table_name}: {e}")
                extraction_stats["failed"] += 1

        # Log summary
        logger.info(
            f"P&L extraction complete: {extraction_stats['successful']} successful, "
            f"{extraction_stats['failed']} failed, {extraction_stats['total_rows']} total rows"
        )

        return results

    async def extract_pnl_constants_tables(
        self, spreadsheet_id: str, engine: str = "polars"
    ) -> Dict[str, Union[pl.DataFrame, pd.DataFrame]]:
        """
        Extract the multiple tables from the constants sheet.

        This is a special case that extracts multiple tables separated by
        3 blank rows from a single sheet.

        Args:
            spreadsheet_id: The P&L spreadsheet ID
            engine: DataFrame engine ('polars' or 'pandas')

        Returns:
            Dictionary with separate DataFrames for each constants table
        """
        # Get raw data from constants sheet
        raw_data = await self.get_sheet_data(spreadsheet_id, "constants")

        # Use multi-table parser
        parser = self.get_parser("constants")
        parsed_table = parser.parse(raw_data, "constants")

        # Extract individual tables based on boundaries
        boundaries = parsed_table.metadata.get("table_boundaries", [])
        tables = {}

        expected_table_names = [
            "labour_constants",
            "account_categories",
            "units",
            "subcontractors",
        ]

        for i, (start_row, end_row, _) in enumerate(boundaries):
            if i < len(expected_table_names):
                table_name = expected_table_names[i]
                table_data = raw_data[start_row : end_row + 1]

                # Parse individual table
                sub_parser = self.get_parser(table_name, "standard")
                sub_table = sub_parser.parse(table_data, table_name)

                # Convert to requested engine
                if engine.lower() == "pandas":
                    df = (
                        sub_table.data.to_pandas()
                        if isinstance(sub_table.data, pl.DataFrame)
                        else sub_table.data
                    )
                else:
                    df = (
                        pl.from_pandas(sub_table.data)
                        if isinstance(sub_table.data, pd.DataFrame)
                        else sub_table.data
                    )

                tables[table_name] = df
                logger.info(
                    f"✅ Constants table '{table_name}': {len(df)} rows × {len(df.columns)} columns"
                )

        logger.info(f"Extracted {len(tables)} constants tables: {list(tables.keys())}")
        return tables

    async def validate_pnl_extraction(
        self, spreadsheet_id: str, tables: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate P&L table extraction without full data download.

        Args:
            spreadsheet_id: The P&L spreadsheet ID
            tables: List of table names to validate

        Returns:
            Dictionary with validation results for each table
        """
        if tables is None:
            tables = list(PNL_PARSER_CONFIGS.keys())

        results = {}

        for table_name in tables:
            try:
                # Get just header and sample data
                raw_data = await self.get_sheet_data(
                    spreadsheet_id,
                    table_name,
                    range_name=f"{table_name}!1:20",  # First 20 rows
                )

                # Use the parser for configuration only
                config = PNL_PARSER_CONFIGS[table_name]

                # Basic validation
                row_count = len(raw_data)
                has_headers = row_count > 0

                validation_result = {
                    "table_exists": has_headers,
                    "sample_row_count": row_count,
                    "parser_type": PNL_PARSER_TYPES[table_name],
                    "expected_columns": config.expected_columns,
                    "expected_min_rows": config.expected_min_rows,
                    "validation_passed": has_headers and row_count >= 2,
                }

                if has_headers and row_count >= 2:
                    # Check headers
                    header_row_idx = (
                        config.header_row - 1 if not config.auto_detect_headers else 0
                    )
                    if header_row_idx < len(raw_data):
                        sample_headers = raw_data[header_row_idx][
                            :10
                        ]  # First 10 columns
                        validation_result["sample_headers"] = sample_headers

                results[table_name] = validation_result
                logger.info(
                    f"✅ Validation for {table_name}: {'PASS' if validation_result['validation_passed'] else 'FAIL'}"
                )

            except Exception as e:
                results[table_name] = {
                    "table_exists": False,
                    "error": str(e),
                    "validation_passed": False,
                }
                logger.error(f"❌ Validation failed for {table_name}: {e}")

        return results


# Convenience function for creating the enhanced client
def create_pnl_client() -> PnLGoogleSheetsClient:
    """Create a P&L-enabled Google Sheets client."""
    return PnLGoogleSheetsClient()
