"""
DEPRECATED: Legacy Google Sheets client.

This module is deprecated. Please use enviroflow_app.gsheets.gsheets.GoogleSheetsClient instead.
This file now provides a compatibility wrapper around the modern implementation.
"""

import warnings
from typing import List, Optional

import polars as pl

# Import the modern implementation
from .gsheets import GoogleSheetsClient

# Issue deprecation warning when this module is imported
warnings.warn(
    "gsheets_client.py is deprecated. Use enviroflow_app.gsheets.GoogleSheetsClient instead.",
    DeprecationWarning,
    stacklevel=2,
)


class GSheetsClient(GoogleSheetsClient):
    """
    Legacy GSheetsClient class - now a wrapper around the modern GoogleSheetsClient.

    This class is deprecated. Please use GoogleSheetsClient directly.
    """

    def __init__(self):
        """Initialize the legacy client using Streamlit secrets."""
        # Always try to initialize with Streamlit secrets for backward compatibility
        super().__init__(credentials=None)

    async def get_sheet_data_legacy(
        self, spreadsheet_name: str, sheet_name: str
    ) -> Optional[List[List[str]]]:
        """
        Legacy method - get sheet data by spreadsheet name.

        Args:
            spreadsheet_name: Name of the spreadsheet
            sheet_name: Name of the sheet

        Returns:
            List of rows as lists (may return None for compatibility)
        """
        try:
            data = await self.get_sheet_data_by_name(spreadsheet_name, sheet_name)
            # Convert to List[List[str]] for backward compatibility
            return [
                [str(cell) if cell is not None else "" for cell in row] for row in data
            ]
        except Exception:
            # For backward compatibility, return None instead of raising
            return None

    async def get_sheet_data_by_url(self, url: str, sheet_name: str) -> List[List[str]]:
        """
        Legacy method - get sheet data by URL.

        Args:
            url: Google Sheets URL
            sheet_name: Name of the sheet

        Returns:
            List of rows as lists
        """
        spreadsheet_id = self._extract_spreadsheet_id(url)
        data = await super().get_sheet_data(spreadsheet_id, sheet_name)
        # Convert to List[List[str]] for backward compatibility
        return [[str(cell) if cell is not None else "" for cell in row] for row in data]

    def list_accessible_sheets(self) -> List[tuple[str, str]]:
        """
        Legacy method - list accessible sheets.

        Returns:
            List of (name, id) tuples
        """
        import asyncio

        async def _list_sheets():
            spreadsheets = await self.list_spreadsheets()
            return [(sheet.title, sheet.spreadsheet_id) for sheet in spreadsheets]

        # Run the async method synchronously for backward compatibility
        return asyncio.run(_list_sheets())

    def get_sheet_by_url(self, url: str) -> dict:
        """
        Legacy method - get sheet metadata by URL.

        Args:
            url: Google Sheets URL

        Returns:
            Sheet metadata dictionary
        """
        import asyncio

        async def _get_sheet():
            spreadsheet_id = self._extract_spreadsheet_id(url)
            info = await self.get_spreadsheet_info(spreadsheet_id)
            # Convert to dict format for backward compatibility
            return {
                "spreadsheetId": info.spreadsheet_id,
                "properties": info.properties or {},
                "sheets": [
                    {
                        "properties": {
                            "title": sheet.title,
                            "sheetId": sheet.sheet_id,
                            "index": sheet.index,
                            "sheetType": sheet.sheet_type,
                            "gridProperties": sheet.grid_properties or {},
                        }
                    }
                    for sheet in info.sheets
                ],
            }

        return asyncio.run(_get_sheet())

    async def parse_sheet_to_polars(
        self, spreadsheet_name: str, sheet_name: str
    ) -> pl.DataFrame:
        """
        Legacy method - parse sheet to Polars by name.

        Args:
            spreadsheet_name: Name of the spreadsheet
            sheet_name: Name of the sheet

        Returns:
            Polars DataFrame
        """
        return await self.parse_sheet_to_polars_by_name(spreadsheet_name, sheet_name)

    async def parse_sheet_to_polars_by_url(
        self, url: str, sheet_name: str
    ) -> pl.DataFrame:
        """
        Legacy method - parse sheet to Polars by URL.

        Args:
            url: Google Sheets URL
            sheet_name: Name of the sheet

        Returns:
            Polars DataFrame
        """
        spreadsheet_id = self._extract_spreadsheet_id(url)
        result = await super().get_sheet_as_dataframe(
            spreadsheet_id, sheet_name, engine="polars"
        )
        # Type check to ensure we return a Polars DataFrame
        if isinstance(result, pl.DataFrame):
            return result
        else:
            raise TypeError("Expected Polars DataFrame but got pandas DataFrame")
