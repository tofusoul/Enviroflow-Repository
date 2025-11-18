"""
Flexible parsing system for Google Sheets with different table structures.

This module provides injectable parsing functions for handling various table layouts
found in P&L spreadsheets, including standard tables, offset headers, multi-table sheets,
and paginated data.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

import polars as pl
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ParsedTable:
    """Container for parsed table data with metadata."""

    name: str
    data: Union[pl.DataFrame, pd.DataFrame]
    headers: List[str]
    row_count: int
    column_count: int
    parser_used: str
    metadata: Dict[str, Any]


@dataclass
class ParsingConfig:
    """Configuration for table parsing behavior."""

    header_row: int = 1  # Row number containing headers (1-based)
    max_blank_rows: int = 3  # Max consecutive blank rows before stopping
    expected_min_rows: int = 10  # Minimum expected data rows
    expected_columns: Optional[List[str]] = None  # Expected column names
    pagination_size: int = 1000  # Expected page size for pagination detection
    auto_detect_headers: bool = True  # Whether to automatically detect header row


class TableParser(ABC):
    """Abstract base class for table parsers."""

    def __init__(self, config: ParsingConfig):
        self.config = config

    @abstractmethod
    def parse(self, raw_data: List[List[Any]], table_name: str) -> ParsedTable:
        """Parse raw sheet data into a structured table."""
        pass

    @abstractmethod
    def validate(self, parsed_table: ParsedTable) -> bool:
        """Validate that the parsed table meets expectations."""
        pass

    def _detect_header_row(self, raw_data: List[List[Any]]) -> int:
        """
        Detect the most likely header row by finding the row with most non-empty cells.

        Returns:
            1-based row number of detected header
        """
        if not self.config.auto_detect_headers:
            return self.config.header_row

        max_non_empty = 0
        header_row_idx = 0

        # Check first 5 rows for headers
        for i, row in enumerate(raw_data[:5]):
            non_empty_count = sum(1 for cell in row if cell and str(cell).strip())
            if non_empty_count > max_non_empty:
                max_non_empty = non_empty_count
                header_row_idx = i

        return header_row_idx + 1  # Convert to 1-based

    def _clean_headers(self, headers: List[Any]) -> List[str]:
        """Clean and normalize header names."""
        cleaned = []
        for i, header in enumerate(headers):
            if header is None or header == "":
                cleaned.append(f"column_{i}")
            else:
                header_str = str(header).strip()
                if not header_str:
                    cleaned.append(f"column_{i}")
                else:
                    cleaned.append(header_str)
        return cleaned

    def _normalize_rows(
        self, rows: List[List[Any]], target_columns: int
    ) -> List[List[Any]]:
        """Normalize all rows to have the same number of columns."""
        normalized = []
        for row in rows:
            # Extend row to target length
            normalized_row = list(row) + [None] * (target_columns - len(row))
            # Truncate if too long
            normalized_row = normalized_row[:target_columns]
            normalized.append(normalized_row)
        return normalized


class StandardTableParser(TableParser):
    """Parser for standard tables with headers in row 1."""

    def parse(self, raw_data: List[List[Any]], table_name: str) -> ParsedTable:
        """Parse a standard table structure."""
        if not raw_data:
            raise ValueError(f"No data provided for table {table_name}")

        # Detect header row
        header_row_num = self._detect_header_row(raw_data)
        header_row_idx = header_row_num - 1  # Convert to 0-based

        # Extract headers and data
        headers = self._clean_headers(raw_data[header_row_idx])
        data_rows = raw_data[header_row_idx + 1 :]

        if not data_rows:
            logger.warning(
                f"No data rows found after header row {header_row_num} in {table_name}"
            )

        # Normalize row lengths
        max_cols = len(headers)
        normalized_rows = self._normalize_rows(data_rows, max_cols)

        # Clean cells to ensure consistent types for Polars
        cleaned_rows = []
        for row in normalized_rows:
            cleaned_row = [
                None if (cell is None or cell == "") else str(cell) for cell in row
            ]
            cleaned_rows.append(cleaned_row)

        # Create DataFrame with robust inference across all rows
        df = pl.DataFrame(
            cleaned_rows,
            schema=headers,
            orient="row",
            infer_schema_length=len(cleaned_rows) if cleaned_rows else 0,
        )

        return ParsedTable(
            name=table_name,
            data=df,
            headers=headers,
            row_count=len(normalized_rows),
            column_count=len(headers),
            parser_used="standard",
            metadata={
                "header_row": header_row_num,
                "original_row_count": len(raw_data),
                "data_start_row": header_row_num + 1,
            },
        )

    def validate(self, parsed_table: ParsedTable) -> bool:
        """Validate standard table structure."""
        if parsed_table.row_count < self.config.expected_min_rows:
            logger.warning(
                f"Table {parsed_table.name} has {parsed_table.row_count} rows, "
                f"expected at least {self.config.expected_min_rows}"
            )

        if self.config.expected_columns:
            missing_cols = set(self.config.expected_columns) - set(parsed_table.headers)
            if missing_cols:
                logger.warning(
                    f"Missing expected columns in {parsed_table.name}: {missing_cols}"
                )
                return False

        return True


class OffsetHeaderParser(TableParser):
    """Parser for tables with headers in a specific row (not row 1)."""

    def parse(self, raw_data: List[List[Any]], table_name: str) -> ParsedTable:
        """Parse table with headers in a specific offset row."""
        if not raw_data:
            raise ValueError(f"No data provided for table {table_name}")

        # Use configured header row or detect
        if self.config.auto_detect_headers:
            header_row_num = self._detect_header_row(raw_data)
        else:
            header_row_num = self.config.header_row

        header_row_idx = header_row_num - 1  # Convert to 0-based

        if header_row_idx >= len(raw_data):
            raise ValueError(
                f"Header row {header_row_num} not found in {table_name} "
                f"(only {len(raw_data)} rows available)"
            )

        # Extract headers and data
        headers = self._clean_headers(raw_data[header_row_idx])
        data_rows = raw_data[header_row_idx + 1 :]

        # Normalize row lengths
        max_cols = len(headers)
        normalized_rows = self._normalize_rows(data_rows, max_cols)

        # Clean cells for Polars construction
        cleaned_rows = []
        for row in normalized_rows:
            cleaned_row = [
                None if (cell is None or cell == "") else str(cell) for cell in row
            ]
            cleaned_rows.append(cleaned_row)

        # Create DataFrame with robust inference
        df = pl.DataFrame(
            cleaned_rows,
            schema=headers,
            orient="row",
            infer_schema_length=len(cleaned_rows) if cleaned_rows else 0,
        )

        return ParsedTable(
            name=table_name,
            data=df,
            headers=headers,
            row_count=len(normalized_rows),
            column_count=len(headers),
            parser_used="offset_header",
            metadata={
                "header_row": header_row_num,
                "original_row_count": len(raw_data),
                "data_start_row": header_row_num + 1,
                "skipped_rows": header_row_idx,
            },
        )

    def validate(self, parsed_table: ParsedTable) -> bool:
        """Validate offset header table."""
        # Use the same validation logic as StandardTableParser
        if parsed_table.row_count < self.config.expected_min_rows:
            logger.warning(
                f"Table {parsed_table.name} has {parsed_table.row_count} rows, "
                f"expected at least {self.config.expected_min_rows}"
            )

        if self.config.expected_columns:
            missing_cols = set(self.config.expected_columns) - set(parsed_table.headers)
            if missing_cols:
                logger.warning(
                    f"Missing expected columns in {parsed_table.name}: {missing_cols}"
                )
                return False

        return True


class MultiTableParser(TableParser):
    """Parser for sheets containing multiple tables separated by blank rows."""

    def parse(self, raw_data: List[List[Any]], table_name: str) -> ParsedTable:
        """Parse multiple tables from a single sheet."""
        if not raw_data:
            raise ValueError(f"No data provided for table {table_name}")

        # Find table boundaries by looking for separator rows
        table_boundaries = self._find_table_boundaries(raw_data)

        # Parse each table
        tables = {}
        for i, (start_row, end_row, table_suffix) in enumerate(table_boundaries):
            table_data = raw_data[start_row : end_row + 1]

            # Use standard parser for each subtable
            sub_parser = StandardTableParser(self.config)
            sub_table = sub_parser.parse(table_data, f"{table_name}_{table_suffix}")
            tables[table_suffix] = sub_table

        # Combine metadata from all tables
        combined_metadata = {
            "table_count": len(tables),
            "table_boundaries": table_boundaries,
            "subtables": {name: table.metadata for name, table in tables.items()},
        }

        # For now, return the first table as the primary result
        # In a full implementation, this might return a MultiTable container
        primary_table = next(iter(tables.values()))
        primary_table.name = table_name
        primary_table.parser_used = "multi_table"
        primary_table.metadata.update(combined_metadata)

        return primary_table

    def _find_table_boundaries(
        self, raw_data: List[List[Any]]
    ) -> List[Tuple[int, int, str]]:
        """
        Find table boundaries separated by blank rows.

        Returns:
            List of (start_row, end_row, table_name) tuples
        """
        boundaries = []
        current_start = None
        blank_count = 0
        table_count = 0

        for i, row in enumerate(raw_data):
            is_blank = not any(cell and str(cell).strip() for cell in row)

            if is_blank:
                blank_count += 1
                if (
                    blank_count >= self.config.max_blank_rows
                    and current_start is not None
                ):
                    # End of table found
                    boundaries.append(
                        (current_start, i - blank_count, f"table_{table_count}")
                    )
                    current_start = None
                    table_count += 1
            else:
                if current_start is None:
                    current_start = i  # Start of new table
                blank_count = 0

        # Handle last table
        if current_start is not None:
            boundaries.append(
                (current_start, len(raw_data) - 1, f"table_{table_count}")
            )

        return boundaries

    def validate(self, parsed_table: ParsedTable) -> bool:
        """Validate multi-table structure."""
        if "table_count" not in parsed_table.metadata:
            logger.warning(
                f"Multi-table parser did not find multiple tables in {parsed_table.name}"
            )
            return False

        table_count = parsed_table.metadata["table_count"]
        if table_count < 2:
            logger.warning(
                f"Expected multiple tables in {parsed_table.name}, found {table_count}"
            )

        return True


class PaginatedTableParser(StandardTableParser):
    """Parser for tables that may be truncated due to pagination limits."""

    def parse(self, raw_data: List[List[Any]], table_name: str) -> ParsedTable:
        """Parse table and check for pagination issues."""
        parsed_table = super().parse(raw_data, table_name)

        # Check for pagination issues
        row_count = parsed_table.row_count
        if self.config.pagination_size <= 0:
            is_likely_paginated = False
        else:
            delta = row_count % self.config.pagination_size
            # Consider both ends of the boundary window (low and high)
            threshold = 10
            is_likely_paginated = row_count > 0 and (
                delta < threshold
                or delta > max(0, self.config.pagination_size - threshold)
            )

        parsed_table.parser_used = "paginated"
        parsed_table.metadata.update(
            {
                "likely_paginated": is_likely_paginated,
                "pagination_size": self.config.pagination_size,
                "pagination_warning": is_likely_paginated,
            }
        )

        if is_likely_paginated:
            logger.warning(
                f"Table {table_name} has {row_count} rows which suggests pagination truncation "
                f"(near {self.config.pagination_size} boundary)"
            )

        return parsed_table

    def validate(self, parsed_table: ParsedTable) -> bool:
        """Validate paginated table with special attention to row counts."""
        base_valid = super().validate(parsed_table)

        if parsed_table.metadata.get("likely_paginated", False):
            logger.error(
                f"CRITICAL: Table {parsed_table.name} appears to be truncated by pagination. "
                f"Row count: {parsed_table.row_count}"
            )
            return False

        return base_valid


class ParserFactory:
    """Factory for creating appropriate parsers based on table configuration."""

    PARSER_REGISTRY = {
        "standard": StandardTableParser,
        "offset_header": OffsetHeaderParser,
        "multi_table": MultiTableParser,
        "standard_paginated": PaginatedTableParser,
    }

    @classmethod
    def create_parser(cls, parser_type: str, config: ParsingConfig) -> TableParser:
        """Create a parser of the specified type."""
        if parser_type not in cls.PARSER_REGISTRY:
            raise ValueError(f"Unknown parser type: {parser_type}")

        parser_class = cls.PARSER_REGISTRY[parser_type]
        return parser_class(config)

    @classmethod
    def register_parser(cls, name: str, parser_class: type):
        """Register a custom parser type."""
        cls.PARSER_REGISTRY[name] = parser_class


# P&L specific parser configurations based on TODO requirements
PNL_PARSER_CONFIGS = {
    "costs": ParsingConfig(
        header_row=1,
        expected_min_rows=10000,
        expected_columns=[
            "Date",
            "Account",
            "gen_proj",
            "Debit",
            "Credit",
            "Gross",
            "net",
            "GST",
        ],
        pagination_size=1000,
        auto_detect_headers=True,
    ),
    "constants": ParsingConfig(
        header_row=1, max_blank_rows=3, expected_min_rows=10, auto_detect_headers=True
    ),
    "report_scope_projects": ParsingConfig(
        header_row=2,  # Headers specifically in row 2
        expected_min_rows=500,
        expected_columns=["name", "jan_24", "feb_24", "mar_24", "apr_24"],
        auto_detect_headers=False,  # Don't auto-detect, use row 2
    ),
    "xero_name": ParsingConfig(
        header_row=1,
        expected_min_rows=100,
        expected_columns=["xero_name", "Project"],
        auto_detect_headers=True,
    ),
    "sales": ParsingConfig(
        header_row=1, expected_min_rows=1000, auto_detect_headers=True
    ),
    "quotes": ParsingConfig(
        header_row=1, expected_min_rows=1000, auto_detect_headers=True
    ),
    "pricing_table": ParsingConfig(
        header_row=1, expected_min_rows=100, auto_detect_headers=True
    ),
}

# P&L parser type mapping
PNL_PARSER_TYPES = {
    "costs": "standard_paginated",  # Critical: needs pagination fix
    "constants": "multi_table",  # Multiple tables separated by 3 blank rows
    "report_scope_projects": "offset_header",  # Headers in row 2
    "xero_name": "standard",
    "sales": "standard",
    "quotes": "standard",
    "pricing_table": "standard",
}


def create_pnl_parser(table_name: str) -> TableParser:
    """
    Create a pre-configured parser for P&L tables.

    Args:
        table_name: Name of the P&L table (e.g., 'costs', 'constants')

    Returns:
        Configured parser for the specified table

    Raises:
        ValueError: If table_name is not recognized
    """
    if table_name not in PNL_PARSER_CONFIGS:
        raise ValueError(f"Unknown P&L table: {table_name}")

    config = PNL_PARSER_CONFIGS[table_name]
    parser_type = PNL_PARSER_TYPES[table_name]

    return ParserFactory.create_parser(parser_type, config)
