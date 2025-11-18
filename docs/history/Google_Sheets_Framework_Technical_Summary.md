# Google Sheets Parsing Framework

## Overview

The Google Sheets parsing framework provides a comprehensive, flexible system for extracting data from Google Sheets with different table structures. It addresses real-world challenges such as headers in non-standard rows, multiple tables per sheet, pagination detection, and SSL issues in WSL environments.

## Architecture

### Core Components

1. **GoogleSheetsClient** (`enviroflow_app/gsheets/gsheets.py`)
   - Base client with authentication and data fetching
   - WSL SSL configuration and bypass
   - Intelligent header detection
   - Pagination handling

2. **Parser Framework** (`enviroflow_app/gsheets/parsers.py`)
   - Abstract `TableParser` base class
   - Specialized parser implementations
   - Factory pattern for parser creation

3. **P&L Enhanced Client** (`enviroflow_app/gsheets/pnl_client.py`)
   - Pre-configured parsers for P&L tables
   - Batch extraction methods
   - Specialized handling for multi-table sheets

## Parser Types

### 1. StandardTableParser
- **Use Case:** Standard tables with headers in row 1
- **Features:** Basic table parsing with intelligent header detection
- **Example Tables:** `sales`, `xero_name`, `quotes`, `pricing_table`

### 2. OffsetHeaderParser
- **Use Case:** Tables with headers not in row 1
- **Configuration:** `header_row` parameter (0-indexed)
- **Example:** `report_scope_projects` (headers in row 2, configured as `header_row=1`)

### 3. MultiTableParser
- **Use Case:** Sheets containing multiple tables separated by blank rows
- **Features:** Automatically detects table boundaries and extracts all tables
- **Example:** `constants` sheet with `labour_constants`, `account_categories`, `units`, `subcontractors`
- **Separation Detection:** Configurable number of consecutive blank rows (default: 3)

### 4. PaginatedTableParser
- **Use Case:** Large tables that may be truncated by pagination
- **Features:** Detects pagination patterns and warns if truncation suspected
- **Example:** `costs` table (should have ~13k records, not 999)
- **Detection:** Configurable row threshold and round number detection

## P&L Table Configurations

### Pre-configured Parsers

```python
# Standard Tables
"sales": StandardTableParser(),
"xero_name": StandardTableParser(),
"quotes": StandardTableParser(),
"pricing_table": StandardTableParser(),

# Offset Header Table
"report_scope_projects": OffsetHeaderParser(header_row=1),  # Headers in row 2

# Multi-table Sheet
"constants": MultiTableParser(min_blank_rows=3),

# Large Paginated Table
"costs": PaginatedTableParser(pagination_threshold=1000)
```

### Table Mapping
| Source Sheet | Target MotherDuck Table | Parser Type | Notes |
|-------------|------------------------|-------------|-------|
| `costs` | `pnl_costs` | PaginatedTableParser | ~13k records, pagination critical |
| `constants` | `pnl_constants_*` | MultiTableParser | 4 tables: labour_constants, account_categories, units, subcontractors |
| `report_scope_projects` | `pnl_report_scope_projects` | OffsetHeaderParser | Headers in row 2 |
| `xero_name` | `pnl_xero_name` | StandardTableParser | Standard structure |
| `sales` | `pnl_sales` | StandardTableParser | Standard structure |
| `quotes` | `pnl_original_quotes` | StandardTableParser | Renamed for clarity |
| `pricing_table` | `pnl_pricing_table` | StandardTableParser | Standard structure |

## Technical Features

### WSL SSL Handling
The framework automatically detects WSL environments and applies SSL workarounds:
```python
# Auto-detection and configuration
if self._is_wsl():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
```

### Intelligent Header Detection
Automatic detection of header rows with fallback strategies:
```python
def _detect_headers(self, data: List[List[Any]]) -> int:
    """Detect header row by finding first non-empty row with text content"""
    for i, row in enumerate(data):
        if any(cell and str(cell).strip() for cell in row):
            return i
    return 0
```

### Pagination Detection
Smart detection of truncated data:
```python
def _detect_pagination(self, record_count: int) -> bool:
    """Detect if table may be paginated/truncated"""
    if record_count >= self.pagination_threshold:
        # Check for round numbers that suggest pagination
        if record_count % 100 == 0 or record_count % 250 == 0:
            return True
    return False
```

## Usage Examples

### Basic P&L Table Extraction
```python
from enviroflow_app.gsheets.pnl_client import PnLGoogleSheetsClient

client = PnLGoogleSheetsClient()

# Extract single table
df = client.extract_pnl_table("costs")

# Extract all tables
all_tables = client.extract_all_pnl_tables()

# Extract multi-table constants
constants_tables = client.extract_pnl_constants_tables()
```

### Custom Parser Usage
```python
from enviroflow_app.gsheets.parsers import OffsetHeaderParser

# Custom parser for headers in row 3
custom_parser = OffsetHeaderParser(header_row=2)
df = client.extract_table_with_parser("custom_sheet", custom_parser)
```

### Error Handling and Validation
```python
try:
    df = client.extract_pnl_table("costs")

    # Check for pagination issues
    if len(df) == 999:
        logger.warning("Costs table may be truncated - expected ~13k records")

except Exception as e:
    logger.error(f"Failed to extract P&L table: {e}")
```

## Testing Framework

### Comprehensive Test Suite
- **File:** `tests/test_gsheets_client.py`
- **Coverage:** Authentication, data consistency, pagination, multiple engines
- **Real-world Validation:** All edge cases from development sessions

### Parser Framework Tests
- **File:** `tests/test_pnl_parsers.py`
- **Coverage:** All parser types, P&L configurations, integration scenarios

### Key Test Categories
1. **Authentication Tests:** Service account validation
2. **Data Consistency:** Multiple extraction engine comparison
3. **Pagination Detection:** Large table handling
4. **Header Detection:** Various header row scenarios
5. **Multi-table Parsing:** Constants sheet validation
6. **Performance Tests:** Timing and efficiency validation

## Integration Points

### CLI Integration
```bash
# Future CLI command for P&L extraction
python -m enviroflow_app.cli.main extract pnl-tables
```

### MotherDuck Loading
Tables loaded with `pnl_` prefix for clear namespace separation:
- Raw P&L data: `pnl_costs`, `pnl_sales`, etc.
- Transformed data: `costs`, `sales`, etc. (existing pipeline targets)

### Pipeline Integration
The framework replaces legacy static file dependencies:
- **Before:** Read from version-controlled CSV/Parquet files
- **After:** Live extraction from Google Sheets → MotherDuck → Pipeline

## Development History

### Problems Solved
1. **SSL Issues in WSL:** Automatic detection and bypass configuration
2. **Header Detection:** Intelligent scanning for non-standard header positions
3. **Pagination Bugs:** Detection and warning for truncated large tables
4. **Multi-table Sheets:** Automatic table boundary detection
5. **Test Coverage:** Comprehensive validation of all real-world scenarios

### Framework Evolution
1. **Phase 1:** Basic Google Sheets client with authentication
2. **Phase 2:** SSL fixes and header detection improvements
3. **Phase 3:** Injectable parser framework with abstract base class
4. **Phase 4:** Specialized parsers for different table structures
5. **Phase 5:** P&L-specific client with pre-configured parsers
6. **Phase 6:** Comprehensive test suite with all validation scenarios

## Future Enhancements

### Planned Improvements
1. **Dynamic Configuration:** YAML-based parser configuration files
2. **Caching Layer:** Smart caching for unchanged sheets
3. **Incremental Updates:** Change detection and partial updates
4. **Parallel Extraction:** Async processing for multiple tables
5. **Data Validation:** Schema validation against expected structures

### Performance Optimizations
1. **Batch Processing:** Group multiple table requests
2. **Connection Pooling:** Reuse authenticated connections
3. **Compression:** Handle large tables with streaming
4. **Memory Management:** Efficient handling of large datasets

## Critical Notes

### Production Readiness
- ✅ **SSL Configuration:** Production-ready for WSL environments
- ✅ **Error Handling:** Comprehensive exception handling and logging
- ✅ **Parser Framework:** Flexible and extensible architecture
- ⚠️ **Table Structures:** Need real column names for final validation
- ⚠️ **Pagination Fix:** Critical for costs table (~13k records)

### Maintenance Considerations
1. **Google API Changes:** Monitor for API deprecations
2. **Sheet Structure Changes:** Validate parser configurations
3. **Performance Monitoring:** Track extraction times and failures
4. **Rate Limiting:** Implement exponential backoff for API limits
