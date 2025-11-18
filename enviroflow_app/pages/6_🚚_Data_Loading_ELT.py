"""Data Loading ELT Pipeline Interface - Enhanced Version.

A Streamlit page for running the complete ELT pipeline with rich real-time feedback,
step-by-step execution monitoring, progressive table loading, and interactive data exploration.
"""

from datetime import datetime
import traceback
from pathlib import Path
from typing import Any
import streamlit as st

from enviroflow_app.cli.dag import Pipeline, DAGEngine
from enviroflow_app.elt.motherduck.md import MotherDuck
from enviroflow_app.st_components.pipeline_gui import (
    init_pipeline_session_state,
    stream_log,
    display_execution_summary,
    format_results_markdown,
    ExecutionResult,
)

# Page configuration
st.set_page_config(
    layout="wide", page_title="Data Loading ELT Pipeline", page_icon="🚚"
)

# Initialize session state
init_pipeline_session_state()

# Initialize additional session state for enhanced features
if "scheduled_runs_loaded" not in st.session_state:
    st.session_state.scheduled_runs_loaded = False
if "current_step" not in st.session_state:
    st.session_state.current_step = None
if "completed_steps" not in st.session_state:
    st.session_state.completed_steps = []
if "show_pygwalker" not in st.session_state:
    st.session_state.show_pygwalker = False
if "toast_history" not in st.session_state:
    st.session_state.toast_history = []
if "recently_updated_tables" not in st.session_state:
    st.session_state.recently_updated_tables = []


# Helper functions
def load_scheduled_execution_logs() -> None:
    """Load logs from scheduled pipeline executions (10am, 1pm, 6pm)."""
    if st.session_state.scheduled_runs_loaded:
        return

    # Look for ETL logs
    log_dir = Path("logs")
    if not log_dir.exists():
        st.session_state.scheduled_runs_loaded = True
        return

    # Parse etl.log for scheduled runs
    etl_log_path = log_dir / "etl.log"
    if etl_log_path.exists():
        try:
            with open(etl_log_path, "r") as f:
                lines = f.readlines()

                # Look for completion messages from today's scheduled runs
                today = datetime.now().date()
                scheduled_times = ["10:00", "13:00", "18:00"]

                for line in lines[-100:]:  # Check last 100 lines
                    # Parse log format: timestamp | level | message
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 3:
                            timestamp_str = parts[0].strip()
                            message = parts[2].strip()

                            try:
                                log_time = datetime.fromisoformat(timestamp_str)
                                if log_time.date() == today:
                                    # Check if this is a scheduled run
                                    time_str = log_time.strftime("%H:%M")
                                    if any(
                                        sched in time_str for sched in scheduled_times
                                    ):
                                        if (
                                            "completed" in message.lower()
                                            or "success" in message.lower()
                                        ):
                                            stream_log(
                                                "INFO",
                                                "Scheduled Run",
                                                f"📅 Automatic execution at {time_str}: {message}",
                                            )
                            except (ValueError, IndexError):
                                continue
        except Exception as e:
            stream_log("WARNING", "Log Loading", f"Could not parse ETL logs: {str(e)}")

    st.session_state.scheduled_runs_loaded = True


def check_motherduck_connection() -> bool:
    """Check if MotherDuck connection is available.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        token = st.secrets["motherduck"]["token"]
        db_name = st.secrets["motherduck"]["db"]
        md = MotherDuck(token=token, db_name=db_name)
        md.conn.execute("SELECT 1").fetchone()
        return True
    except Exception as e:
        stream_log(
            "ERROR", "Connection Check", f"MotherDuck connection failed: {str(e)}"
        )
        return False


def get_connection_status_message() -> str:
    """Get the connection status message for display.

    Returns:
        Formatted status message with emoji indicator
    """
    if check_motherduck_connection():
        return f"✅ **Connected to MotherDuck**: `{st.secrets['motherduck']['db']}`"
    else:
        return "❌ **Connection Failed**: Unable to connect to MotherDuck"


def get_motherduck_tables() -> list[str]:
    """Get list of tables from MotherDuck catalog.

    Returns:
        List of table names, or empty list if connection fails
    """
    try:
        token = st.secrets["motherduck"]["token"]
        db_name = st.secrets["motherduck"]["db"]
        md = MotherDuck(token=token, db_name=db_name)

        result = md.conn.execute("SHOW TABLES").fetchall()
        tables = [row[0] for row in result]

        # Update session state
        st.session_state.available_tables = tables

        return tables
    except Exception as e:
        stream_log("WARNING", "Table List", f"Could not retrieve table list: {str(e)}")
        return []


def can_start_pipeline() -> bool:
    """Check if pipeline can be started.

    Returns:
        False if pipeline is already running or connection unavailable, True otherwise
    """
    if st.session_state.pipeline_running:
        return False
    if not check_motherduck_connection():
        return False
    return True


def show_step_notification(step_name: str, status: str) -> None:
    """Show a toast notification for step start/completion and persist in session state.

    Args:
        step_name: Name of the pipeline step
        status: 'start', 'complete', or 'error'
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    icon = "ℹ️"  # Default icon
    message = step_name  # Default message

    if status == "start":
        icon = "🔄"
        message = f"Starting: {step_name}"
        st.toast(f"{icon} {message}", icon=icon)
        st.session_state.current_step = step_name

    elif status == "complete":
        icon = "✅"
        message = f"Completed: {step_name}"
        st.toast(f"{icon} {message}", icon=icon)
        if step_name not in st.session_state.completed_steps:
            st.session_state.completed_steps.append(step_name)
        st.session_state.current_step = None

    elif status == "error":
        icon = "❌"
        message = f"Failed: {step_name}"
        st.toast(f"{icon} {message}", icon=icon)
        st.session_state.current_step = None

    # Add to toast history for sidebar persistence (will display after pipeline completes)
    toast_entry = {
        "timestamp": timestamp,
        "icon": icon,
        "status": status,
        "message": message,
    }
    st.session_state.toast_history.append(toast_entry)


def execute_pipeline_with_progress(pipeline: DAGEngine) -> dict[str, Any]:
    """Execute pipeline with step-by-step progress feedback and table loading.

    Args:
        pipeline: The DAG pipeline to execute

    Returns:
        Dictionary of task outputs
    """
    # Validate and get execution order
    pipeline.validate()
    execution_order = pipeline._topological_sort()

    stream_log("INFO", "Pipeline", f"📋 Executing {len(execution_order)} tasks...")

    task_outputs = {}
    successful_tasks = []

    # Pre-announce the first step before loop starts
    if execution_order:
        first_task = pipeline.tasks[execution_order[0]]
        show_step_notification(first_task.description, "start")
        stream_log("INFO", execution_order[0], f"🔄 Starting: {first_task.description}")

    for i, task_name in enumerate(execution_order):
        task = pipeline.tasks[task_name]

        try:
            # Check dependencies
            if not task.can_execute(set(successful_tasks)):
                unsatisfied = task.dependencies - set(successful_tasks)
                stream_log(
                    "WARNING",
                    task_name,
                    f"⏸️ Skipping - unsatisfied dependencies: {unsatisfied}",
                )
                continue

            # Execute task (start notification already shown)
            task_result = task.execute(task_outputs, config=pipeline.config)
            task_outputs.update(task_result)
            successful_tasks.append(task_name)

            # Show completion notification
            show_step_notification(task.description, "complete")
            stream_log("SUCCESS", task_name, f"✅ Completed: {task.description}")

            # Reload tables to show new data and track updated tables
            tables_before = set(st.session_state.get("available_tables", []))
            tables = get_motherduck_tables()
            tables_after = set(tables)

            # Track newly created tables
            new_tables = tables_after - tables_before
            for table_name in new_tables:
                if table_name not in st.session_state.recently_updated_tables:
                    st.session_state.recently_updated_tables.append(table_name)

            stream_log("INFO", task_name, f"📊 {len(tables)} tables now available")

            # Pre-announce NEXT step (if exists) before continuing loop
            if i + 1 < len(execution_order):
                next_task_name = execution_order[i + 1]
                next_task = pipeline.tasks[next_task_name]
                show_step_notification(next_task.description, "start")
                stream_log(
                    "INFO", next_task_name, f"🔄 Starting: {next_task.description}"
                )

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            stream_log("ERROR", task_name, f"❌ Failed: {error_msg}")
            stream_log("ERROR", task_name, f"Traceback: {error_trace}")
            show_step_notification(task.description, "error")
            raise

    return task_outputs


def run_full_pipeline() -> None:
    """Execute the complete ELT pipeline with enhanced real-time feedback."""
    if not can_start_pipeline():
        st.warning("⚠️ Pipeline is already running or connection unavailable")
        return

    # Set running flag
    st.session_state.pipeline_running = True
    st.session_state.current_operation = "Run Full Pipeline"
    st.session_state.operation_start_time = datetime.now()
    st.session_state.completed_steps = []
    st.session_state.toast_history = []  # Clear previous notifications
    st.session_state.recently_updated_tables = []  # Clear previous table tracking

    # Clear previous logs
    st.session_state.execution_log = []

    start_time = datetime.now()

    try:
        stream_log("INFO", "Full Pipeline", "🚀 Starting complete ELT pipeline...")

        # Create pipeline
        pipeline = Pipeline.create_full_pipeline()

        # Execute with progress tracking
        _ = execute_pipeline_with_progress(pipeline)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        stream_log(
            "SUCCESS", "Full Pipeline", f"✅ Pipeline completed in {duration:.1f}s"
        )

        # Get final table list
        tables = get_motherduck_tables()

        # Create execution result
        result: ExecutionResult = {
            "operation": "Run Full Pipeline",
            "status": "success",
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration,
            "records_processed": None,
            "tables_created": tables,
            "validation_results": None,
            "error_message": None,
            "error_traceback": None,
        }

        st.session_state.last_result = result
        st.session_state.operation_history.append(result)

        if len(st.session_state.operation_history) > 20:
            st.session_state.operation_history = st.session_state.operation_history[
                -20:
            ]

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        error_msg = str(e)
        error_trace = traceback.format_exc()

        stream_log("ERROR", "Full Pipeline", f"❌ Pipeline failed: {error_msg}")

        result: ExecutionResult = {
            "operation": "Run Full Pipeline",
            "status": "error",
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration,
            "records_processed": None,
            "tables_created": [],
            "validation_results": None,
            "error_message": error_msg,
            "error_traceback": error_trace,
        }

        st.session_state.last_result = result
        st.session_state.operation_history.append(result)

    finally:
        st.session_state.pipeline_running = False
        st.session_state.current_operation = None
        st.session_state.operation_start_time = None
        st.session_state.current_step = None


# Load scheduled runs on first page load
load_scheduled_execution_logs()

# Page title and description
st.title("🚚 Data Loading ELT Pipeline")
st.markdown("""
Run the complete data pipeline to refresh data from all sources (Trello, Float, Xero, Google Sheets)
and rebuild analytics tables in MotherDuck.
""")

st.divider()

# SIDEBAR: Live Feedback and Execution Summary
with st.sidebar:
    st.header("📊 Live Feedback")

    # Connection status
    status_msg = get_connection_status_message()
    if "✅" in status_msg:
        st.success(status_msg)
    else:
        st.error(status_msg)
        if st.button("🔄 Retry Connection"):
            st.rerun()

    st.divider()

    # Current operation status
    if st.session_state.pipeline_running:
        st.info(f"⏳ **Running**: {st.session_state.current_operation}")
        if st.session_state.current_step:
            st.caption(f"Current step: {st.session_state.current_step}")
        if st.session_state.operation_start_time:
            elapsed = (
                datetime.now() - st.session_state.operation_start_time
            ).total_seconds()
            st.caption(f"Elapsed: {elapsed:.0f}s")

        # Show completed steps
        if st.session_state.completed_steps:
            with st.expander(
                f"✅ Completed Steps ({len(st.session_state.completed_steps)})",
                expanded=False,
            ):
                for step in st.session_state.completed_steps:
                    st.write(f"✓ {step}")

    # Toast notification history
    if st.session_state.toast_history:
        st.divider()
        with st.expander("📬 Recent Notifications", expanded=True):
            # Show last 20 notifications (newest first)
            recent_toasts = st.session_state.toast_history[-20:]
            for toast in reversed(recent_toasts):
                if toast["status"] == "start":
                    st.info(
                        f"**[{toast['timestamp']}]** {toast['icon']} {toast['message']}",
                        icon="🔄",
                    )
                elif toast["status"] == "complete":
                    st.success(
                        f"**[{toast['timestamp']}]** {toast['icon']} {toast['message']}",
                        icon="✅",
                    )
                else:  # error
                    st.error(
                        f"**[{toast['timestamp']}]** {toast['icon']} {toast['message']}",
                        icon="❌",
                    )

    # Display execution summary
    if st.session_state.last_result:
        st.divider()
        st.subheader("📈 Execution Summary")
        display_execution_summary(st.session_state.last_result)

        # Copy results button
        with st.expander("📋 Copy Results", expanded=False):
            formatted_results = format_results_markdown(st.session_state.last_result)
            st.code(formatted_results, language="markdown")

# MAIN AREA: Control Panel
st.header("⚙️ Control Panel")

st.markdown("""
**Run Full Pipeline**
Executes the complete ELT pipeline:
- Extract data from Trello, Float, Xero, Google Sheets
- Transform and build analytics tables
- Validate data quality
""")

can_run = can_start_pipeline()

if st.button(
    "🚀 Run Full Pipeline",
    type="primary",
    disabled=not can_run,
    use_container_width=True,
):
    run_full_pipeline()
    st.rerun()

# Data Exploration Section
st.divider()
st.header("📊 Explore Results")

if st.session_state.available_tables:
    # Filter tables to recently updated ones (if available)
    all_tables = st.session_state.available_tables
    recent_tables = st.session_state.get("recently_updated_tables", [])

    if recent_tables:
        # Show only recently updated tables
        filtered_tables = [t for t in all_tables if t in recent_tables]
        display_tables = filtered_tables if filtered_tables else all_tables

        st.success(
            f"✅ {len(display_tables)} recently updated tables available for exploration"
        )
        st.caption(
            f"💡 Showing tables from the most recent pipeline run. Total tables: {len(all_tables)}"
        )
    else:
        # No recent run - show all tables with info message
        display_tables = all_tables
        st.success(f"✅ {len(display_tables)} tables available for exploration")
        st.info("💡 Run the pipeline to see only recently updated tables here.")

    # Table selector
    selected_table = st.selectbox(
        "Select a table to explore:",
        options=display_tables,
        index=0 if display_tables else None,
    )

    if selected_table:
        col_preview, col_explore = st.columns([1, 1])

        with col_preview:
            # Table preview
            with st.expander("👀 Preview Table (first 100 rows)", expanded=False):
                try:
                    token = st.secrets["motherduck"]["token"]
                    db_name = st.secrets["motherduck"]["db"]
                    md = MotherDuck(token=token, db_name=db_name)

                    # Get row count
                    count_result = md.conn.execute(
                        f"SELECT COUNT(*) FROM {selected_table}"
                    ).fetchone()
                    row_count = count_result[0] if count_result else 0

                    st.caption(f"Total rows: {row_count:,}")

                    # Load first 100 rows
                    query = f"SELECT * FROM {selected_table} LIMIT 100"
                    df = md.conn.execute(query).pl()

                    st.dataframe(df, use_container_width=True, height=400)

                except Exception as e:
                    st.error(f"Error loading table preview: {str(e)}")

        with col_explore:
            # PyGWalker integration
            if st.button("🔍 Open Interactive Explorer", use_container_width=True):
                st.session_state.show_pygwalker = True

        # Show PyGWalker if button clicked
        if st.session_state.get("show_pygwalker", False):
            try:
                from pygwalker.api.streamlit import StreamlitRenderer

                token = st.secrets["motherduck"]["token"]
                db_name = st.secrets["motherduck"]["db"]
                md = MotherDuck(token=token, db_name=db_name)

                # Load data for exploration (limit to 10000 rows for performance)
                query = f"SELECT * FROM {selected_table} LIMIT 10000"
                df_polars = md.conn.execute(query).pl()

                # Convert to pandas, handling array columns
                df_pandas = df_polars.to_pandas()

                # Fix numpy array columns that cause unhashable type error
                for col in df_pandas.columns:
                    if df_pandas[col].dtype == object:
                        # Check if first non-null value is a numpy array
                        sample = (
                            df_pandas[col].dropna().iloc[0]
                            if len(df_pandas[col].dropna()) > 0
                            else None
                        )
                        if sample is not None and hasattr(sample, "__array__"):
                            # Convert arrays to strings
                            df_pandas[col] = df_pandas[col].apply(
                                lambda x: str(x) if x is not None else None
                            )

                st.subheader(f"📊 Interactive Explorer: {selected_table}")
                st.caption("Loaded first 10,000 rows for interactive exploration")

                # Create PyGWalker renderer
                pyg_app = StreamlitRenderer(df_pandas)
                pyg_app.explorer()

            except Exception as e:
                st.error(f"Error loading PyGWalker: {str(e)}")
                st.caption("Make sure pygwalker is installed: `pip install pygwalker`")
                # Show full traceback for debugging
                st.code(traceback.format_exc())
else:
    st.info("📭 No tables available yet. Run the pipeline to populate data.")
