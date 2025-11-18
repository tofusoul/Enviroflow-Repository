"""
Modern Google Sheets integration for Enviroflow App.

This module provides a clean, async interface for accessing Google Sheets
using the official Google Sheets API v4. It supports both service account
and user authentication, with automatic credential management.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

import pandas as pd
import polars as pl
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger


@dataclass
class SheetInfo:
    """Information about a Google Sheet."""

    name: str
    sheet_id: int
    title: str
    index: int
    sheet_type: str
    grid_properties: Optional[Dict[str, Any]] = None


@dataclass
class SpreadsheetInfo:
    """Information about a Google Spreadsheet."""

    spreadsheet_id: str
    title: str
    url: str
    sheets: List[SheetInfo] = field(default_factory=list)
    properties: Optional[Dict[str, Any]] = None


class GoogleSheetsError(Exception):
    """Custom exception for Google Sheets operations."""

    pass


class GoogleSheetsClient:
    """
    Modern Google Sheets client with async support.

    Provides a clean, user-friendly interface for accessing Google Sheets
    with automatic credential management and async operations.
    """

    def __init__(
        self,
        credentials: Optional[
            Union[service_account.Credentials, Dict[str, Any]]
        ] = None,
        scopes: Optional[List[str]] = None,
    ):
        """
        Initialize the Google Sheets client.

        Args:
            credentials: Service account credentials or credentials dict
            scopes: OAuth scopes for the API
        """
        self.scopes = scopes or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        # Initialize credentials
        if credentials is None:
            # Try to load from environment or default location
            self._init_credentials_from_env()
        elif isinstance(credentials, dict):
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials, scopes=self.scopes
            )
        else:
            self.credentials = credentials

        # Build the Google Sheets and Drive services
        try:
            self.service = build("sheets", "v4", credentials=self.credentials)
            self.drive_service = build("drive", "v3", credentials=self.credentials)
        except Exception as e:
            logger.error(f"Service creation failed: {e}")
            raise e

        logger.info("Google Sheets client initialized successfully")

    def _init_credentials_from_env(self) -> None:
        """Initialize credentials from environment or secrets."""
        import os
        import json

        # Try environment variable first (for GitHub Actions)
        gcp_service_account_json = os.getenv("GCP_SERVICE_ACCOUNT")
        if gcp_service_account_json:
            try:
                service_account_info = json.loads(gcp_service_account_json)
                self.credentials = (
                    service_account.Credentials.from_service_account_info(
                        service_account_info, scopes=self.scopes
                    )
                )
                logger.info(
                    "Loaded credentials from GCP_SERVICE_ACCOUNT environment variable"
                )
                return
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GCP_SERVICE_ACCOUNT JSON: {e}")

        try:
            # Try to import streamlit secrets
            import streamlit as st

            if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
                self.credentials = (
                    service_account.Credentials.from_service_account_info(
                        st.secrets["gcp_service_account"], scopes=self.scopes
                    )
                )
                logger.info("Loaded credentials from Streamlit secrets")
                return
        except ImportError:
            pass

        # Try to load from service account file
        service_account_paths = [
            Path("service-account.json"),
            Path("~/.config/gcloud/application_default_credentials.json").expanduser(),
        ]

        for path in service_account_paths:
            if path.exists():
                self.credentials = (
                    service_account.Credentials.from_service_account_file(
                        str(path), scopes=self.scopes
                    )
                )
                logger.info(f"Loaded credentials from {path}")
                return

        raise GoogleSheetsError(
            "No credentials found. Please provide credentials or set up service account file."
        )

    def _extract_spreadsheet_id(self, url_or_id: str) -> str:
        """Extract spreadsheet ID from URL or return if already an ID."""
        if url_or_id.startswith("http"):
            match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_or_id)
            if not match:
                raise GoogleSheetsError(f"Invalid Google Sheets URL: {url_or_id}")
            return match.group(1)
        return url_or_id

    async def list_spreadsheets(self) -> List[SpreadsheetInfo]:
        """
        List all accessible spreadsheets.

        Returns:
            List of spreadsheet information
        """
        try:
            # Use asyncio to run the sync API call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.drive_service.files()
                .list(
                    q="mimeType='application/vnd.google-apps.spreadsheet'",
                    spaces="drive",
                    fields="files(id, name, webViewLink)",
                    pageSize=1000,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute(),
            )

            spreadsheets = []
            for file in response.get("files", []):
                spreadsheet_info = await self.get_spreadsheet_info(file["id"])
                spreadsheets.append(spreadsheet_info)

            logger.info(f"Found {len(spreadsheets)} accessible spreadsheets")
            return spreadsheets

        except HttpError as error:
            logger.error(f"Error listing spreadsheets: {error}")
            raise GoogleSheetsError(f"Failed to list spreadsheets: {error}")

    async def get_spreadsheet_info(self, spreadsheet_id: str) -> SpreadsheetInfo:
        """
        Get detailed information about a spreadsheet.

        Args:
            spreadsheet_id: The spreadsheet ID or URL

        Returns:
            Spreadsheet information
        """
        try:
            spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_id)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id)
                .execute(),
            )

            sheets = []
            for sheet in response.get("sheets", []):
                sheet_props = sheet.get("properties", {})
                sheets.append(
                    SheetInfo(
                        name=sheet_props.get("title", ""),
                        sheet_id=sheet_props.get("sheetId", 0),
                        title=sheet_props.get("title", ""),
                        index=sheet_props.get("index", 0),
                        sheet_type=sheet_props.get("sheetType", ""),
                        grid_properties=sheet_props.get("gridProperties"),
                    )
                )

            return SpreadsheetInfo(
                spreadsheet_id=spreadsheet_id,
                title=response.get("properties", {}).get("title", ""),
                url=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
                sheets=sheets,
                properties=response.get("properties"),
            )

        except HttpError as error:
            logger.error(f"Error getting spreadsheet info: {error}")
            raise GoogleSheetsError(f"Failed to get spreadsheet info: {error}")

    async def get_sheet_data(
        self,
        spreadsheet_id: str,
        sheet_name: Optional[str] = None,
        range_name: Optional[str] = None,
        value_render_option: str = "UNFORMATTED_VALUE",
    ) -> List[List[Any]]:
        """
        Get data from a specific sheet.

        Args:
            spreadsheet_id: The spreadsheet ID or URL
            sheet_name: Name of the sheet (if not provided, uses first sheet)
            range_name: Specific range (e.g., "A1:Z1000")
            value_render_option: How to render values ("UNFORMATTED_VALUE", "FORMATTED_VALUE", "FORMULA")

        Returns:
            List of rows as lists
        """
        try:
            spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_id)

            # Determine the range
            if range_name:
                if not sheet_name:
                    # Extract sheet name from range if possible
                    if "!" in range_name:
                        sheet_name, range_name = range_name.split("!", 1)
                    else:
                        sheet_name = None
            else:
                if sheet_name:
                    range_name = sheet_name  # Fetch the entire sheet
                else:
                    range_name = None  # Fetch all data if possible

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueRenderOption=value_render_option,
                )
                .execute(),
            )

            values = response.get("values", [])
            logger.info(f"Retrieved {len(values)} rows from sheet")
            return values

        except HttpError as error:
            logger.error(f"Error getting sheet data: {error}")
            raise GoogleSheetsError(f"Failed to get sheet data: {error}")

    def _prepare_data_for_polars(
        self, data: List[List[Any]]
    ) -> Tuple[List[str], List[List[Any]]]:
        """
        Prepare data for polars conversion by handling ragged rows and mixed types.

        Args:
            data: Raw sheet data

        Returns:
            Tuple of (headers, cleaned_rows)
        """
        if not data:
            return [], []

        # Find the actual header row by looking for the row with the most non-empty cells
        header_row_idx = 0
        max_non_empty = 0

        for i, row in enumerate(data[:5]):  # Check first 5 rows for headers
            non_empty_count = sum(1 for cell in row if cell and str(cell).strip())
            if non_empty_count > max_non_empty:
                max_non_empty = non_empty_count
                header_row_idx = i

        # Use the identified header row and ensure they are strings
        raw_headers = data[header_row_idx]
        headers = []
        for i, header in enumerate(raw_headers):
            if header is None or header == "":
                headers.append(f"column_{i}")
            else:
                # Convert header to string and clean it
                header_str = str(header).strip()
                if not header_str:
                    headers.append(f"column_{i}")
                else:
                    headers.append(header_str)

        rows = data[header_row_idx + 1 :]

        if not rows:
            return headers, []

        # Find maximum number of columns
        max_cols = max(len(row) for row in rows)
        if len(headers) < max_cols:
            # Extend headers with generic names
            for i in range(len(headers), max_cols):
                headers.append(f"column_{i}")

        # Ensure all headers are unique
        seen = set()
        unique_headers = []
        for header in headers:
            if header in seen:
                count = 1
                new_header = f"{header}_{count}"
                while new_header in seen:
                    count += 1
                    new_header = f"{header}_{count}"
                unique_headers.append(new_header)
                seen.add(new_header)
            else:
                unique_headers.append(header)
                seen.add(header)

        # Pad rows to uniform length and convert to strings to avoid type issues
        cleaned_rows = []
        for row in rows:
            # Pad row to match header length
            padded_row = row + [None] * (len(unique_headers) - len(row))

            # Convert all values to strings to avoid type conversion issues
            cleaned_row = []
            for cell in padded_row:
                if cell is None or cell == "":
                    cleaned_row.append(None)
                else:
                    cleaned_row.append(str(cell))

            cleaned_rows.append(cleaned_row)

        return unique_headers, cleaned_rows

    async def get_sheet_as_dataframe(
        self,
        spreadsheet_id: str,
        sheet_name: Optional[str] = None,
        range_name: Optional[str] = None,
        engine: str = "pandas",
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """
        Get sheet data as a DataFrame.

        Args:
            spreadsheet_id: The spreadsheet ID or URL
            sheet_name: Name of the sheet
            range_name: Specific range
            engine: DataFrame engine ("pandas" or "polars")

        Returns:
            DataFrame with the sheet data
        """
        data = await self.get_sheet_data(spreadsheet_id, sheet_name, range_name)

        if not data:
            raise GoogleSheetsError("No data found in sheet")

        if engine.lower() == "pandas":
            # Use robust pandas conversion similar to polars
            headers, cleaned_rows = self._prepare_data_for_polars(data)
            df = pd.DataFrame(cleaned_rows, columns=headers)
            return df
        elif engine.lower() == "polars":
            # Use robust polars conversion with full schema inference
            headers, cleaned_rows = self._prepare_data_for_polars(data)
            df = pl.DataFrame(
                cleaned_rows,
                schema=headers,
                orient="row",
                infer_schema_length=len(cleaned_rows) if cleaned_rows else 1000,
            )
            return df
        else:
            raise ValueError(f"Unsupported engine: {engine}")

    async def get_all_sheets_as_dataframes(
        self, spreadsheet_id: str, engine: str = "pandas"
    ) -> Dict[str, Union[pd.DataFrame, pl.DataFrame]]:
        """
        Get all sheets in a spreadsheet as DataFrames.

        Args:
            spreadsheet_id: The spreadsheet ID or URL
            engine: DataFrame engine ("pandas" or "polars")

        Returns:
            Dictionary mapping sheet names to DataFrames
        """
        spreadsheet_info = await self.get_spreadsheet_info(spreadsheet_id)
        dataframes = {}

        for sheet in spreadsheet_info.sheets:
            try:
                df = await self.get_sheet_as_dataframe(
                    spreadsheet_id, sheet.name, engine=engine
                )
                dataframes[sheet.name] = df
                logger.info(f"Loaded sheet '{sheet.name}' with {len(df)} rows")
            except Exception as e:
                logger.warning(f"Failed to load sheet '{sheet.name}': {e}")
                continue

        return dataframes

    async def search_spreadsheets(self, query: str) -> List[SpreadsheetInfo]:
        """
        Search for spreadsheets by name.

        Args:
            query: Search query

        Returns:
            List of matching spreadsheets
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.drive_service.files()
                .list(
                    q=f"name contains '{query}' and mimeType='application/vnd.google-apps.spreadsheet'",
                    spaces="drive",
                    fields="files(id, name, webViewLink)",
                    pageSize=1000,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute(),
            )

            spreadsheets = []
            for file in response.get("files", []):
                spreadsheet_info = await self.get_spreadsheet_info(file["id"])
                spreadsheets.append(spreadsheet_info)

            logger.info(f"Found {len(spreadsheets)} spreadsheets matching '{query}'")
            return spreadsheets

        except HttpError as error:
            logger.error(f"Error searching spreadsheets: {error}")
            raise GoogleSheetsError(f"Failed to search spreadsheets: {error}")

    async def get_spreadsheet_names(self) -> List[str]:
        """
        Get list of all accessible spreadsheet names (similar to old collection_names).

        Returns:
            List of spreadsheet names
        """
        try:
            spreadsheets = await self.list_spreadsheets()
            return [sheet.title for sheet in spreadsheets]
        except Exception as e:
            logger.error(f"Error getting spreadsheet names: {e}")
            return []

    async def get_spreadsheet_by_name(self, name: str) -> Optional[SpreadsheetInfo]:
        """
        Get a specific spreadsheet by name.

        Args:
            name: Spreadsheet name

        Returns:
            Spreadsheet info or None if not found
        """
        try:
            spreadsheets = await self.list_spreadsheets()
            for sheet in spreadsheets:
                if sheet.title == name:
                    return sheet
            return None
        except Exception as e:
            logger.error(f"Error getting spreadsheet by name: {e}")
            return None

    async def get_named_ranges(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """
        Get all named ranges in a spreadsheet (these can represent tables).

        Args:
            spreadsheet_id: The spreadsheet ID or URL

        Returns:
            List of named ranges
        """
        try:
            spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_id)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id, ranges=[], includeGridData=False)
                .execute(),
            )

            named_ranges = response.get("namedRanges", [])
            logger.info(f"Found {len(named_ranges)} named ranges")
            return named_ranges

        except HttpError as error:
            logger.error(f"Error getting named ranges: {error}")
            raise GoogleSheetsError(f"Failed to get named ranges: {error}")

    async def get_table_data_by_named_range(
        self, spreadsheet_id: str, named_range_name: str, engine: str = "pandas"
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """
        Get data from a named range (which can represent a table).

        Args:
            spreadsheet_id: The spreadsheet ID or URL
            named_range_name: Name of the named range
            engine: DataFrame engine ("pandas" or "polars")

        Returns:
            DataFrame with the table data
        """
        try:
            # Get the named range to find its range
            named_ranges = await self.get_named_ranges(spreadsheet_id)

            target_range = None
            for named_range in named_ranges:
                if named_range.get("name") == named_range_name:
                    target_range = named_range.get("range")
                    break

            if not target_range:
                raise GoogleSheetsError(f"Named range '{named_range_name}' not found")

            # Get data using the named range
            data = await self.get_sheet_data(spreadsheet_id, range_name=target_range)

            if not data:
                raise GoogleSheetsError("No data found in named range")

            # Use first row as headers
            headers = data[0]
            rows = data[1:]

            if engine.lower() == "pandas":
                df = pd.DataFrame(rows, columns=headers)
                return df
            elif engine.lower() == "polars":
                df = pl.DataFrame(
                    rows,
                    schema=headers,
                    orient="row",
                    infer_schema_length=len(rows) if rows else 1000,
                )
                return df
            else:
                raise ValueError(f"Unsupported engine: {engine}")

        except Exception as e:
            logger.error(f"Error getting table data by named range: {e}")
            raise GoogleSheetsError(f"Failed to get table data: {e}")

    async def get_protected_ranges(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """
        Get all protected ranges in a spreadsheet (can contain table data).

        Args:
            spreadsheet_id: The spreadsheet ID or URL

        Returns:
            List of protected ranges
        """
        try:
            spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_id)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id, ranges=[], includeGridData=False)
                .execute(),
            )

            protected_ranges = []
            for sheet in response.get("sheets", []):
                sheet_protected_ranges = sheet.get("protectedRanges", [])
                for protected_range in sheet_protected_ranges:
                    protected_range["sheetTitle"] = sheet.get("properties", {}).get(
                        "title", ""
                    )
                protected_ranges.extend(sheet_protected_ranges)

            logger.info(f"Found {len(protected_ranges)} protected ranges")
            return protected_ranges

        except HttpError as error:
            logger.error(f"Error getting protected ranges: {error}")
            raise GoogleSheetsError(f"Failed to get protected ranges: {error}")

    async def get_data_validation_rules(
        self, spreadsheet_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get data validation rules which can define table structures.

        Args:
            spreadsheet_id: The spreadsheet ID or URL

        Returns:
            List of data validation rules
        """
        try:
            spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_id)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id, ranges=[], includeGridData=True)
                .execute(),
            )

            validation_rules = []
            for sheet in response.get("sheets", []):
                sheet_data = sheet.get("data", [])
                for grid_data in sheet_data:
                    row_data = grid_data.get("rowData", [])
                    for row_index, row in enumerate(row_data):
                        values = row.get("values", [])
                        for col_index, value in enumerate(values):
                            if "dataValidation" in value:
                                validation_rules.append(
                                    {
                                        "sheetTitle": sheet.get("properties", {}).get(
                                            "title", ""
                                        ),
                                        "row": row_index,
                                        "col": col_index,
                                        "validation": value["dataValidation"],
                                    }
                                )

            logger.info(f"Found {len(validation_rules)} data validation rules")
            return validation_rules

        except HttpError as error:
            logger.error(f"Error getting data validation rules: {error}")
            raise GoogleSheetsError(f"Failed to get data validation rules: {error}")

    async def detect_table_ranges(
        self, spreadsheet_id: str, sheet_name: str
    ) -> List[Dict[str, Any]]:
        """
        Automatically detect table-like structures in a sheet.

        Args:
            spreadsheet_id: The spreadsheet ID or URL
            sheet_name: Name of the sheet

        Returns:
            List of detected table ranges
        """
        try:
            # Get all data from the sheet
            data = await self.get_sheet_data(spreadsheet_id, sheet_name)

            if not data or len(data) < 2:
                return []

            tables = []
            current_table = None

            for row_index, row in enumerate(data):
                # Check if this row looks like a header (has data and next row has data)
                if row and any(cell for cell in row) and row_index < len(data) - 1:
                    next_row = data[row_index + 1]
                    if next_row and any(cell for cell in next_row):
                        # This might be a table header
                        if current_table is None:
                            current_table = {
                                "start_row": row_index,
                                "headers": row,
                                "data_rows": [],
                            }
                        else:
                            # Add data row to current table
                            current_table["data_rows"].append(row)
                else:
                    # End of table
                    if current_table and len(current_table["data_rows"]) > 0:
                        current_table["end_row"] = row_index - 1
                        current_table["range"] = (
                            f"{sheet_name}!A{current_table['start_row'] + 1}:{chr(65 + len(current_table['headers']) - 1)}{current_table['end_row'] + 1}"
                        )
                        tables.append(current_table)
                        current_table = None

            # Don't forget the last table
            if current_table and len(current_table["data_rows"]) > 0:
                current_table["end_row"] = len(data) - 1
                current_table["range"] = (
                    f"{sheet_name}!A{current_table['start_row'] + 1}:{chr(65 + len(current_table['headers']) - 1)}{current_table['end_row'] + 1}"
                )
                tables.append(current_table)

            logger.info(
                f"Detected {len(tables)} table-like structures in sheet '{sheet_name}'"
            )
            return tables

        except Exception as e:
            logger.error(f"Error detecting table ranges: {e}")
            return []

    async def get_table_data_by_detection(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        table_index: int = 0,
        engine: str = "pandas",
    ) -> Union[pd.DataFrame, pl.DataFrame]:
        """
        Get data from a detected table in a sheet.

        Args:
            spreadsheet_id: The spreadsheet ID or URL
            sheet_name: Name of the sheet
            table_index: Index of the table to get (0 for first table)
            engine: DataFrame engine ("pandas" or "polars")

        Returns:
            DataFrame with the table data
        """
        try:
            # Detect tables in the sheet
            tables = await self.detect_table_ranges(spreadsheet_id, sheet_name)

            if not tables:
                raise GoogleSheetsError(f"No tables detected in sheet '{sheet_name}'")

            if table_index >= len(tables):
                raise GoogleSheetsError(
                    f"Table index {table_index} out of range. Found {len(tables)} tables."
                )

            table = tables[table_index]

            # Create DataFrame from table data
            headers = table["headers"]
            rows = table["data_rows"]

            if engine.lower() == "pandas":
                df = pd.DataFrame(rows, columns=headers)
                return df
            elif engine.lower() == "polars":
                # Use robust polars conversion for table data
                # Prepare data with headers and rows
                table_data = [headers] + rows
                headers_clean, cleaned_rows = self._prepare_data_for_polars(table_data)
                df = pl.DataFrame(
                    cleaned_rows,
                    schema=headers_clean,
                    orient="row",
                    infer_schema_length=len(cleaned_rows) if cleaned_rows else 1000,
                )
                return df
            else:
                raise ValueError(f"Unsupported engine: {engine}")

        except Exception as e:
            logger.error(f"Error getting table data by detection: {e}")
            raise GoogleSheetsError(f"Failed to get table data: {e}")


# Convenience functions for easy access
async def get_sheet_data(
    spreadsheet_id: str,
    sheet_name: Optional[str] = None,
    credentials: Optional[Union[service_account.Credentials, Dict[str, Any]]] = None,
) -> List[List[Any]]:
    """
    Quick function to get sheet data.

    Args:
        spreadsheet_id: The spreadsheet ID or URL
        sheet_name: Name of the sheet
        credentials: Optional credentials

    Returns:
        List of rows as lists
    """
    client = GoogleSheetsClient(credentials)
    return await client.get_sheet_data(spreadsheet_id, sheet_name)


async def get_sheet_as_dataframe(
    spreadsheet_id: str,
    sheet_name: Optional[str] = None,
    engine: str = "pandas",
    credentials: Optional[Union[service_account.Credentials, Dict[str, Any]]] = None,
) -> Union[pd.DataFrame, pl.DataFrame]:
    """
    Quick function to get sheet as DataFrame.

    Args:
        spreadsheet_id: The spreadsheet ID or URL
        sheet_name: Name of the sheet
        engine: DataFrame engine ("pandas" or "polars")
        credentials: Optional credentials

    Returns:
        DataFrame with the sheet data
    """
    client = GoogleSheetsClient(credentials)
    return await client.get_sheet_as_dataframe(
        spreadsheet_id, sheet_name, engine=engine
    )


async def list_accessible_spreadsheets(
    credentials: Optional[Union[service_account.Credentials, Dict[str, Any]]] = None,
) -> List[SpreadsheetInfo]:
    """
    Quick function to list accessible spreadsheets.

    Args:
        credentials: Optional credentials

    Returns:
        List of spreadsheet information
    """
    client = GoogleSheetsClient(credentials)
    return await client.list_spreadsheets()
