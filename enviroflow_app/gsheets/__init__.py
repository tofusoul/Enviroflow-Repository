"""
Google Sheets integration module for ELT operations.

This module provides async Google Sheets access for data extraction and loading,
including specialized P&L table parsing with injectable parser framework.
"""

from .gsheets import (
    GoogleSheetsClient,
    GoogleSheetsError,
    SheetInfo,
    SpreadsheetInfo,
    get_sheet_as_dataframe,
    get_sheet_data,
    list_accessible_spreadsheets,
)

from .parsers import (
    ParsedTable,
    ParsingConfig,
    TableParser,
    StandardTableParser,
    OffsetHeaderParser,
    MultiTableParser,
    PaginatedTableParser,
    ParserFactory,
    create_pnl_parser,
    PNL_PARSER_CONFIGS,
    PNL_PARSER_TYPES,
)

from .pnl_client import (
    PnLGoogleSheetsClient,
    create_pnl_client,
)

__all__ = [
    # Base Google Sheets functionality
    "GoogleSheetsClient",
    "GoogleSheetsError",
    "SheetInfo",
    "SpreadsheetInfo",
    "get_sheet_as_dataframe",
    "get_sheet_data",
    "list_accessible_spreadsheets",
    # Parser framework
    "ParsedTable",
    "ParsingConfig",
    "TableParser",
    "StandardTableParser",
    "OffsetHeaderParser",
    "MultiTableParser",
    "PaginatedTableParser",
    "ParserFactory",
    "create_pnl_parser",
    "PNL_PARSER_CONFIGS",
    "PNL_PARSER_TYPES",
    # P&L enhanced client
    "PnLGoogleSheetsClient",
    "create_pnl_client",
]
