import logging
from typing import List

import polars as pl
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(level=logging.DEBUG)


class GSheetsClient:
    def __init__(self):
        logging.debug("Initializing GSheetsClient with credentials from st.secrets")
        self.credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        self.service = build("sheets", "v4", credentials=self.credentials)

    async def get_sheet_data(
        self, spreadsheet_name: str, sheet_name: str
    ) -> List[List[str]]:
        logging.debug(
            f"Fetching data from spreadsheet: {spreadsheet_name}, sheet: {sheet_name}"
        )
        try:
            spreadsheet_id = self._get_spreadsheet_id(spreadsheet_name)
            logging.debug(f"Spreadsheet ID: {spreadsheet_id}")
            range_name = f"{sheet_name}!A1:Z1000"
            logging.debug("Attempting to call Google Sheets API...")
            logging.debug(f"Range requested: {range_name}")
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            logging.debug(f"Raw response from Google Sheets API: {result}")
            return result.get("values", [])
        except HttpError as error:
            logging.exception(f"An error occurred: {error}")
            return None

    async def get_sheet_data_by_url(self, url: str, sheet_name: str) -> List[List[str]]:
        """Fetch data from a Google Sheet using its URL."""
        logging.debug(f"Fetching data from sheet '{sheet_name}' using URL: {url}")
        try:
            # Extract the spreadsheet ID from the URL
            import re

            match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
            if not match:
                raise ValueError("Invalid Google Sheet URL")

            spreadsheet_id = match.group(1)
            logging.debug(f"Extracted Spreadsheet ID: {spreadsheet_id}")

            # Define the range to fetch data from
            range_name = f"{sheet_name}!A1:Z1000"  # Adjust range as needed
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            logging.debug(f"Data fetched: {result}")
            return result.get("values", [])
        except HttpError as error:
            logging.exception(
                f"An error occurred while accessing the sheet by URL: {error}"
            )
            raise

    def _get_spreadsheet_id(self, spreadsheet_name: str) -> str:
        logging.debug(f"Searching for spreadsheet ID by name: {spreadsheet_name}")
        try:
            drive_service = build("drive", "v3", credentials=self.credentials)
            query = f"name='{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
            response = (
                drive_service.files()
                .list(q=query, spaces="drive", fields="files(id, name)")
                .execute()
            )
            logging.debug(f"Querying Google Drive API with query: {query}")
            logging.debug(f"Response from Google Drive API: {response}")
            files = response.get("files", [])

            if not files:
                logging.warning(
                    f"Spreadsheet with name '{spreadsheet_name}' not found."
                )
                raise ValueError(
                    f"Spreadsheet with name '{spreadsheet_name}' not found."
                )

            logging.debug(f"Spreadsheet found: {files[0]}")
            return files[0]["id"]
        except HttpError as error:
            logging.exception(
                f"An error occurred while fetching spreadsheet ID: {error}"
            )
            raise

    def list_accessible_sheets(self) -> List[tuple[str, str]]:
        """List all Google Sheets the service account has access to."""
        logging.debug("Listing all accessible Google Sheets.")
        try:
            drive_service = build("drive", "v3", credentials=self.credentials)
            query = "mimeType='application/vnd.google-apps.spreadsheet'"
            response = (
                drive_service.files()
                .list(q=query, spaces="drive", fields="files(id, name)")
                .execute()
            )
            files = response.get("files", [])

            if not files:
                logging.info(
                    "No Google Sheets found accessible to the service account."
                )
                return []

            logging.debug(f"Accessible Google Sheets: {files}")
            return [(file["name"], file["id"]) for file in files]
        except HttpError as error:
            logging.exception(f"An error occurred while listing Google Sheets: {error}")
            raise

    def get_sheet_by_url(self, url: str) -> dict:
        """Access a Google Sheet by its URL."""
        logging.debug(f"Accessing Google Sheet by URL: {url}")
        try:
            # Extract the spreadsheet ID from the URL
            import re

            match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
            if not match:
                raise ValueError("Invalid Google Sheet URL")

            spreadsheet_id = match.group(1)
            logging.debug(f"Extracted Spreadsheet ID: {spreadsheet_id}")

            # Fetch the metadata of the spreadsheet to confirm access
            spreadsheet = (
                self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            )
            logging.debug(f"Spreadsheet metadata: {spreadsheet}")

            return spreadsheet
        except HttpError as error:
            logging.exception(
                f"An error occurred while accessing the sheet by URL: {error}"
            )
            raise

    async def parse_sheet_to_polars(
        self, spreadsheet_name: str, sheet_name: str
    ) -> pl.DataFrame:
        """Fetch data from a Google Sheet and parse it into a Polars DataFrame."""
        logging.debug(
            f"Parsing sheet '{sheet_name}' from spreadsheet '{spreadsheet_name}' into a Polars DataFrame."
        )
        try:
            data = await self.get_sheet_data(spreadsheet_name, sheet_name)
            if not data:
                raise ValueError(
                    f"No data found in sheet '{sheet_name}' of spreadsheet '{spreadsheet_name}'."
                )

            # Infer column names from the first row
            column_names = data[0]
            rows = data[1:]

            # Ensure all rows match the number of columns in the header
            num_columns = len(column_names)
            rows = [
                row[:num_columns] + [None] * (num_columns - len(row)) for row in rows
            ]

            # Print adjusted rows for debugging
            print("Adjusted rows:", rows[:5])

            # Create a Polars DataFrame
            df = pl.DataFrame(rows, schema=column_names)
            logging.debug(f"Raw data fetched from sheet: {data}")
            logging.debug(
                f"Successfully parsed data into Polars DataFrame: {df.head()}."
            )
            return df
        except Exception as e:
            logging.exception(f"Error parsing sheet to Polars DataFrame: {e}")
            raise

    async def parse_sheet_to_polars_by_url(
        self, url: str, sheet_name: str
    ) -> pl.DataFrame:
        """Fetch data from a Google Sheet by URL and parse it into a Polars DataFrame."""
        logging.debug(
            f"Parsing sheet '{sheet_name}' from URL: {url} into a Polars DataFrame."
        )
        try:
            # Fetch data using the URL
            data = await self.get_sheet_data_by_url(url, sheet_name)
            if not data:
                raise ValueError(
                    f"No data found in sheet '{sheet_name}' from URL: {url}."
                )

            # Print raw data for debugging
            logging.debug(f"Raw data fetched from sheet: {data}")

            # Infer column names from the first row
            column_names = data[0]

            # Ensure column names are unique
            seen = set()
            unique_column_names = []
            for col in column_names:
                if col in seen:
                    count = 1
                    new_col = f"{col}_{count}"
                    while new_col in seen:
                        count += 1
                        new_col = f"{col}_{count}"
                    unique_column_names.append(new_col)
                    seen.add(new_col)
                else:
                    unique_column_names.append(col)
                    seen.add(col)

            rows = data[1:]

            # Validate row lengths and log invalid rows
            valid_rows = []
            for i, row in enumerate(rows):
                if len(row) == len(unique_column_names):
                    valid_rows.append(row)
                else:
                    logging.warning(f"Row {i + 1} has a mismatched length: {row}")

            # Log detailed information about valid and invalid rows
            logging.debug(f"Total rows fetched: {len(rows)}")
            logging.debug(f"Number of valid rows: {len(valid_rows)}")
            logging.debug(f"Number of invalid rows: {len(rows) - len(valid_rows)}")

            if not valid_rows:
                raise ValueError("No valid rows found to create a DataFrame.")

            # Create a Polars DataFrame and infer types
            df = pl.DataFrame(valid_rows, schema=unique_column_names)

            # Log the inferred schema for debugging
            logging.debug(f"Inferred DataFrame schema: {df.schema}")

            return df
        except Exception as e:
            logging.exception(f"Error parsing sheet to Polars DataFrame: {e}")
            raise

    async def parse_specific_table(
        self, url: str, sheet_name: str, expected_schema: List[str]
    ) -> pl.DataFrame:
        """Parse a specific table from a Google Sheet into a Polars DataFrame with a defined schema."""
        logging.debug(
            f"Parsing specific table from sheet '{sheet_name}' with expected schema: {expected_schema}"
        )
        try:
            # Fetch data using the URL
            data = await self.get_sheet_data_by_url(url, sheet_name)
            if not data:
                raise ValueError(
                    f"No data found in sheet '{sheet_name}' from URL: {url}."
                )

            # Print raw data for debugging
            logging.debug(
                f"Raw data fetched from sheet: {data[:5]} (showing first 5 rows)"
            )

            # Normalize rows to match the expected schema length
            num_columns = len(expected_schema)
            normalized_rows = [
                row[:num_columns] + [None] * (num_columns - len(row))
                for row in data[1:]  # Skip the header row
            ]

            # Validate rows and log invalid ones
            valid_rows = []
            for i, row in enumerate(normalized_rows):
                if len(row) == num_columns:
                    valid_rows.append(row)
                else:
                    logging.warning(f"Row {i + 1} has a mismatched length: {row}")

            if not valid_rows:
                raise ValueError("No valid rows found to create a DataFrame.")

            # Create a Polars DataFrame with the expected schema
            df = pl.DataFrame(valid_rows, schema=expected_schema)

            # Log the inferred schema for debugging
            logging.debug(f"Inferred DataFrame schema: {df.schema}")

            return df
        except Exception as e:
            logging.exception(f"Error parsing specific table: {e}")
            raise
