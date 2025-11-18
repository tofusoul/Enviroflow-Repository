"""Pipeline GUI Components for Streamlit.

This module provides reusable components for the Data Loading ELT page,
including session state management, log streaming, and result display
for pipeline execution.
"""

from datetime import datetime
from typing import TypedDict, Any
import streamlit as st
from enviroflow_app.st_components.st_logger import Log_Level, st_logger


# Type definitions for data structures
class LogMessage(TypedDict):
    """Structure for a single log message from pipeline execution."""

    timestamp: datetime
    level: str  # "info" | "success" | "warning" | "error"
    operation: str
    message: str
    details: dict[str, Any] | None


class ExecutionResult(TypedDict):
    """Structure for pipeline execution results."""

    operation: str
    status: str  # "success" | "warning" | "error"
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    records_processed: int | None
    tables_created: list[str]
    validation_results: dict[str, Any] | None
    error_message: str | None
    error_traceback: str | None


# Color scheme constants for log levels
LOG_COLORS = {
    "INFO": "🔵",
    "SUCCESS": "✅",
    "WARNING": "⚠️",
    "ERROR": "❌",
}


def init_pipeline_session_state() -> None:
    """Initialize all session state keys required for pipeline GUI.

    This function sets up the session state with default values for:
    - pipeline_running: Flag to prevent concurrent executions
    - execution_log: List of log messages for current session
    - last_result: Most recent execution result
    - operation_history: Session history of completed operations (last 20)
    - available_tables: List of table names from MotherDuck catalog

    Follows patterns from enviroflow_app/st_components/pre.py
    """
    if "pipeline_running" not in st.session_state:
        st_logger(Log_Level.INFO, "📦 Initializing pipeline_running in session state")
        st.session_state.pipeline_running = False

    if "execution_log" not in st.session_state:
        st_logger(Log_Level.INFO, "📦 Initializing execution_log in session state")
        st.session_state.execution_log = []

    if "last_result" not in st.session_state:
        st_logger(Log_Level.INFO, "📦 Initializing last_result in session state")
        st.session_state.last_result = None

    if "operation_history" not in st.session_state:
        st_logger(Log_Level.INFO, "📦 Initializing operation_history in session state")
        st.session_state.operation_history = []

    if "available_tables" not in st.session_state:
        st_logger(Log_Level.INFO, "📦 Initializing available_tables in session state")
        st.session_state.available_tables = []

    if "current_operation" not in st.session_state:
        st_logger(Log_Level.INFO, "📦 Initializing current_operation in session state")
        st.session_state.current_operation = None

    if "operation_start_time" not in st.session_state:
        st_logger(
            Log_Level.INFO, "📦 Initializing operation_start_time in session state"
        )
        st.session_state.operation_start_time = None


def stream_log(
    level: str,
    operation: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Append a log message to the execution log in session state.

    Args:
        level: Log level - "INFO", "SUCCESS", "WARNING", or "ERROR"
        operation: Name of the operation generating the log
        message: Human-readable log message
        details: Optional structured data (e.g., record counts)

    Example:
        stream_log("INFO", "Extract Trello", "🔗 Connecting to Trello API...")
        stream_log("SUCCESS", "Extract Trello", "✅ Extracted 247 job cards",
                   {"record_count": 247})
    """
    log_entry: LogMessage = {
        "timestamp": datetime.now(),
        "level": level.upper(),
        "operation": operation,
        "message": message,
        "details": details,
    }

    st.session_state.execution_log.append(log_entry)


def display_execution_summary(result: ExecutionResult) -> None:
    """Display a summary card for completed pipeline execution.

    Args:
        result: ExecutionResult dictionary containing operation details

    Shows:
        - Operation name and status badge (✅/⚠️/❌)
        - Duration in seconds
        - Records processed (if applicable)
        - Tables created/updated with record counts
        - Data quality metrics (valid records, warnings, errors)

    Uses st.success(), st.warning(), or st.error() based on status.
    """
    status = result["status"]
    emoji = LOG_COLORS.get(status.upper(), "ℹ️")

    # Choose appropriate Streamlit component based on status
    if status == "success":
        container_func = st.success
    elif status == "warning":
        container_func = st.warning
    else:  # error
        container_func = st.error

    # Build summary message
    summary_lines = [
        f"### {emoji} {result['operation']}",
        f"**Duration**: {result['duration_seconds']:.1f} seconds",
    ]

    if result["records_processed"] is not None:
        summary_lines.append(f"**Records Processed**: {result['records_processed']:,}")

    if result["tables_created"]:
        summary_lines.append(
            f"**Tables Updated**: {', '.join(result['tables_created'])}"
        )

    if result["validation_results"]:
        val = result["validation_results"]
        summary_lines.append(
            f"**Validation**: {val.get('valid_records', 0)} valid, "
            f"{val.get('warnings', 0)} warnings, {val.get('errors', 0)} errors"
        )

    if result["error_message"]:
        summary_lines.append(f"\n**Error**: {result['error_message']}")

    container_func("\n\n".join(summary_lines))


def format_results_markdown(result: ExecutionResult) -> str:
    """Generate a Markdown-formatted summary for easy copying.

    Args:
        result: ExecutionResult dictionary

    Returns:
        Formatted Markdown string suitable for pasting into emails,
        Slack, or documents

    Example output:
        ## Pipeline Execution Summary
        Operation: Extract Trello Data
        Status: ✅ Success
        Duration: 27.3 seconds
        Records Processed: 247 job cards

        ### Results
        - Extracted: 247 job cards
        - Saved to: MotherDuck table 'job_cards'
        - Validation: ✅ All records valid
    """
    status_emoji = LOG_COLORS.get(result["status"].upper(), "ℹ️")

    lines = [
        "## Pipeline Execution Summary",
        f"**Operation**: {result['operation']}",
        f"**Status**: {status_emoji} {result['status'].title()}",
        f"**Duration**: {result['duration_seconds']:.1f} seconds",
    ]

    if result["records_processed"] is not None:
        lines.append(f"**Records Processed**: {result['records_processed']:,}")

    if result["tables_created"]:
        lines.append("\n### Tables Created/Updated")
        for table in result["tables_created"]:
            lines.append(f"- `{table}`")

    if result["validation_results"]:
        val = result["validation_results"]
        lines.append("\n### Validation Results")
        lines.append(f"- Valid records: {val.get('valid_records', 0):,}")
        lines.append(f"- Warnings: {val.get('warnings', 0)}")
        lines.append(f"- Errors: {val.get('errors', 0)}")

    if result["error_message"]:
        lines.append("\n### Error Details")
        lines.append(f"```\n{result['error_message']}\n```")

    return "\n".join(lines)
