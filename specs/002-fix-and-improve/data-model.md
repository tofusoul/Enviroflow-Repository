# Data Model: Data Pipeline GUI Controller

## Overview
This document defines the data structures and state management for the Data Pipeline GUI Controller. The feature is primarily a UI wrapper, so the "data model" focuses on UI state management rather than business entities.

## 1. Session State Schema

The GUI uses Streamlit session state to track execution status, logs, and results across page reruns.

### Core Execution State

```python
# Pipeline execution control
ss.pipeline_running: bool = False
    # True when any pipeline operation is executing
    # Prevents concurrent operations
    # Reset to False when operation completes

ss.current_operation: str | None = None
    # Name of the currently running operation (e.g., "Extract Trello Data")
    # None when no operation is running
    # Used for status display and locking

ss.operation_start_time: datetime | None = None
    # Timestamp when current operation started
    # Used to calculate duration
    # Reset when operation completes
```

### Log Message Structure

```python
ss.execution_log: list[LogMessage] = []
    # Append-only list of log messages for current session
    # Automatically scrolled to show latest
    # Persists across page reruns until session ends

LogMessage = {
    "timestamp": datetime,          # When log message was created
    "level": str,                   # "info" | "success" | "warning" | "error"
    "operation": str,               # Which operation generated this log
    "message": str,                 # Human-readable log text
    "details": dict | None,         # Optional structured data (e.g., record counts)
}

# Example log messages:
{
    "timestamp": datetime(2025, 10, 2, 14, 30, 15),
    "level": "info",
    "operation": "Extract Trello Data",
    "message": "🔗 Connecting to Trello API...",
    "details": None
}

{
    "timestamp": datetime(2025, 10, 2, 14, 30, 42),
    "level": "success",
    "operation": "Extract Trello Data",
    "message": "✅ Extracted 247 job cards",
    "details": {"record_count": 247, "table": "job_cards"}
}
```

### Execution Results

```python
ss.last_result: ExecutionResult | None = None
    # Result from most recently completed operation
    # Displayed in results panel
    # Overwritten by each new operation

ExecutionResult = {
    "operation": str,               # Operation name
    "status": str,                  # "success" | "warning" | "error"
    "start_time": datetime,         # When operation started
    "end_time": datetime,           # When operation completed
    "duration_seconds": float,      # Calculated duration
    "records_processed": int | None,# Number of records affected (if applicable)
    "tables_created": list[str],    # List of table names created/updated
    "validation_results": dict | None,  # Validation metrics if applicable
    "error_message": str | None,    # Error details if status == "error"
    "error_traceback": str | None,  # Full traceback for debugging
}

# Example result:
{
    "operation": "Extract Trello Data",
    "status": "success",
    "start_time": datetime(2025, 10, 2, 14, 30, 15),
    "end_time": datetime(2025, 10, 2, 14, 30, 42),
    "duration_seconds": 27.3,
    "records_processed": 247,
    "tables_created": ["job_cards", "raw_boards"],
    "validation_results": {"valid_records": 247, "warnings": 0, "errors": 0},
    "error_message": None,
    "error_traceback": None,
}
```

### Operation History

```python
ss.operation_history: list[ExecutionResult] = []
    # Session history of all completed operations
    # Displayed in expandable history section
    # Limited to last 20 operations to avoid memory bloat
```

### Data Exploration State

```python
ss.available_tables: list[str] = []
    # List of table names available for exploration
    # Updated after each operation completes
    # Queried from MotherDuck catalog

ss.selected_table_for_preview: str | None = None
    # User-selected table to preview/explore
    # Drives PyGWalker data loading
```

## 2. Pipeline Operation Definitions

Operations are statically defined (not database-driven). This metadata drives UI generation.

**Note**: The individual operation definitions below (extract_trello, transform_quotes, etc.) are documented here for **future Priority 2 implementation**. The **MVP only implements one operation: "Run Full Pipeline"** which executes all operations via `Pipeline.create_full_pipeline().execute()`.

```python
PipelineOperation = {
    "id": str,                      # Unique identifier (e.g., "extract_trello")
    "display_name": str,            # User-facing name (e.g., "Extract Trello Data")
    "category": str,                # "extract" | "transform" | "validate"
    "description": str,             # What this operation does
    "function": callable,           # Actual function to execute
    "dependencies": list[str],      # Operation IDs that must run first
    "estimated_duration_sec": int,  # Rough estimate for user expectation
    "outputs": list[str],           # Table names produced
}

# Example operations (hardcoded in page):
PIPELINE_OPERATIONS = [
    {
        "id": "extract_trello",
        "display_name": "Extract Trello Data",
        "category": "extract",
        "description": "Fetch job cards and board data from Trello API",
        "function": extraction_ops.extract_trello_data,
        "dependencies": [],
        "estimated_duration_sec": 20,
        "outputs": ["job_cards", "raw_boards"],
    },
    {
        "id": "extract_float",
        "display_name": "Extract Float Data",
        "category": "extract",
        "description": "Fetch labour hours and time tracking from Float API",
        "function": extraction_ops.extract_float_data,
        "dependencies": [],
        "estimated_duration_sec": 30,
        "outputs": ["labour_hours", "raw_float"],
    },
    {
        "id": "extract_xero_costs",
        "display_name": "Extract Xero Costs",
        "category": "extract",
        "description": "Fetch cost data from Google Sheets P&L (13,652+ records)",
        "function": extraction_ops.extract_xero_costs,
        "dependencies": [],
        "estimated_duration_sec": 60,
        "outputs": ["xero_costs"],
    },
    {
        "id": "extract_sales",
        "display_name": "Extract Sales Data",
        "category": "extract",
        "description": "Fetch sales data from Google Sheets P&L (30,996+ records)",
        "function": extraction_ops.extract_sales_data,
        "dependencies": [],
        "estimated_duration_sec": 60,
        "outputs": ["xero_sales"],
    },
    {
        "id": "transform_quotes",
        "display_name": "Build Quotes Table",
        "category": "transform",
        "description": "Merge and normalize Xero and Simpro quotes",
        "function": transform_ops.build_quotes_table,
        "dependencies": [],  # Uses legacy data
        "estimated_duration_sec": 10,
        "outputs": ["quotes"],
    },
    {
        "id": "transform_jobs",
        "display_name": "Build Jobs Table",
        "category": "transform",
        "description": "Create jobs from job cards and quotes",
        "function": transform_ops.build_jobs_table,
        "dependencies": ["extract_trello", "transform_quotes"],
        "estimated_duration_sec": 15,
        "outputs": ["jobs", "job_quote_mapping"],
    },
    {
        "id": "transform_customers",
        "display_name": "Build Customers Table",
        "category": "transform",
        "description": "Extract unique customers from job cards",
        "function": transform_ops.build_customers_table,
        "dependencies": ["extract_trello"],
        "estimated_duration_sec": 5,
        "outputs": ["customers"],
    },
    {
        "id": "transform_add_labour",
        "display_name": "Add Labour to Jobs",
        "category": "transform",
        "description": "Integrate labour hours with jobs data",
        "function": transform_ops.add_labour_to_jobs,
        "dependencies": ["extract_float", "transform_jobs"],
        "estimated_duration_sec": 10,
        "outputs": ["jobs_with_hours"],
    },
    {
        "id": "transform_projects",
        "display_name": "Build Projects Table",
        "category": "transform",
        "description": "Aggregate jobs and quotes into project analytics",
        "function": transform_ops.build_projects_table,
        "dependencies": ["transform_add_labour", "transform_quotes"],
        "estimated_duration_sec": 15,
        "outputs": ["projects", "projects_for_analytics"],
    },
    {
        "id": "validate_all",
        "display_name": "Run Validation Suite",
        "category": "validate",
        "description": "Validate all pipeline data quality and integrity",
        "function": validation_ops.run_full_validation_suite,
        "dependencies": [],  # Can run anytime after data exists
        "estimated_duration_sec": 30,
        "outputs": [],  # No new tables, just validation report
    },
]
```

## 3. UI Configuration

```python
# Color scheme for log levels (using Streamlit colors)
LOG_LEVEL_CONFIG = {
    "info": {"icon": "🔵", "method": "st.info"},
    "success": {"icon": "✅", "method": "st.success"},
    "warning": {"icon": "⚠️", "method": "st.warning"},
    "error": {"icon": "❌", "method": "st.error"},
}

# Category icons for operation buttons
CATEGORY_ICONS = {
    "extract": "📥",
    "transform": "🔄",
    "validate": "✅",
}

# Layout configuration
LAYOUT_CONFIG = {
    "control_column_width": 0.35,   # 35% width for control panel
    "feedback_column_width": 0.65,  # 65% width for feedback panel
    "max_log_messages": 500,        # Limit log history to prevent memory issues
    "max_history_items": 20,        # Limit operation history
}
```

## 4. Data Flow

### User Initiates Operation

1. User clicks operation button (e.g., "Extract Trello Data")
2. UI checks `ss.pipeline_running`:
   - If `True`: Show "Operation in progress" message, disable button
   - If `False`: Proceed to execution
3. Set `ss.pipeline_running = True`
4. Set `ss.current_operation = "Extract Trello Data"`
5. Set `ss.operation_start_time = now()`
6. Clear `ss.last_result = None`

### During Execution

1. Execute operation function: `result = extraction_ops.extract_trello_data()`
2. Operation function yields log messages (or we capture output)
3. For each log message:
   - Create `LogMessage` object
   - Append to `ss.execution_log`
   - Update feedback panel UI (via `st.empty()` container)
4. UI remains responsive (Streamlit's execution model)

### After Completion

1. Operation returns result or raises exception
2. If successful:
   - Create `ExecutionResult` with `status="success"`
   - Calculate duration: `now() - ss.operation_start_time`
   - Populate result fields (records, tables, validation)
3. If error:
   - Create `ExecutionResult` with `status="error"`
   - Capture error message and traceback
4. Set `ss.last_result = execution_result`
5. Append `execution_result` to `ss.operation_history`
6. Set `ss.pipeline_running = False`
7. Set `ss.current_operation = None`
8. Query MotherDuck for updated `ss.available_tables`
9. Display result summary in feedback panel

### Full Pipeline Execution

1. Special "Run Full Pipeline" button
2. Executes operations in dependency order (using existing DAG logic from `cli/dag/pipeline.py`)
3. Same log/result tracking as individual operations
4. Single consolidated result at end

## 5. MotherDuck Integration

The GUI reads from MotherDuck to show available tables and enables exploration.

```python
# Get MotherDuck connection (reuse existing pattern)
md_conn = ss.db_conn  # Already initialized by pre.init_default_session()

# Query available tables after operations
available_tables = md_conn.conn.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'main'
    ORDER BY table_name
""").pl()["table_name"].to_list()

# Load table for preview
table_df = md_conn.get_table(table_name="job_cards")

# Table metadata
table_info = md_conn.conn.execute(f"""
    SELECT COUNT(*) as row_count
    FROM {table_name}
""").pl()
```

## 6. Error Handling Data Flow

### API Connection Errors

```python
try:
    result = extraction_ops.extract_trello_data()
except TrelloConnectionError as e:
    log_message = {
        "level": "error",
        "message": f"❌ Trello API connection failed: {str(e)}",
        "details": {"error_type": "TrelloConnectionError"}
    }
    execution_result = {
        "status": "error",
        "error_message": "Could not connect to Trello API. Check credentials.",
        "error_traceback": traceback.format_exc(),
    }
```

### Data Validation Errors

```python
# Validation operations return structured results
validation_result = validation_ops.run_full_validation_suite()
# validation_result = {
#     "overall_passed": False,
#     "summary": {"total_errors": 3, "total_warnings": 5},
#     "table_results": {...}
# }

if not validation_result["overall_passed"]:
    execution_result["status"] = "warning"  # Completed but with issues
    execution_result["validation_results"] = validation_result
```

### MotherDuck Connection Errors

```python
# Handled by CLI operations automatically (they fall back to local files)
# GUI just displays whatever the operation logs
# Example log from operation:
#   "⚠️ MotherDuck unavailable, saving to local files"
#   "💾 Saved to Data/cli_pipeline_data/processed_parquet/job_cards.parquet"
```

## 7. Testing Data Structures

Integration tests will use mock session state and verify state transitions.

```python
# Test fixture: Mock session state
@pytest.fixture
def mock_session_state():
    return {
        "pipeline_running": False,
        "current_operation": None,
        "execution_log": [],
        "last_result": None,
        "operation_history": [],
        "db_conn": MockMotherDuckConnection(),
    }

# Test: Operation execution updates state correctly
def test_extract_trello_updates_session_state(mock_session_state):
    # Setup
    ss = mock_session_state
    operation = PIPELINE_OPERATIONS[0]  # extract_trello

    # Execute
    execute_pipeline_operation(operation, ss)

    # Assert
    assert ss["pipeline_running"] == False  # Reset after completion
    assert ss["last_result"]["status"] == "success"
    assert len(ss["execution_log"]) > 0
    assert ss["last_result"]["operation"] == "Extract Trello Data"
```

## 8. Performance Considerations

### Memory Management

- **Log rotation**: `ss.execution_log` limited to last 500 messages to prevent memory bloat
- **History pruning**: `ss.operation_history` limited to last 20 operations
- **DataFrame cleanup**: DataFrames not stored in session state (only metadata)

### Session Persistence

- Session state survives page reruns (Streamlit default)
- Session cleared when user closes browser tab (Streamlit default)
- Operations continue server-side even if browser closes

### Concurrent Access

- Multiple users get separate sessions (Streamlit default)
- No cross-session interference
- MotherDuck handles concurrent writes (database-level)

## Summary

The data model is intentionally simple:
- **Session state**: Tracks UI state and execution history
- **Static operation definitions**: Hardcoded metadata, not database-driven
- **MotherDuck integration**: Read-only queries for exploration
- **No new business entities**: Feature wraps existing pipeline logic

This simplicity aligns with the constitution's simplicity-first principle and makes the feature easy to maintain and test.
