"""
# Business Data Explorer

A Streamlit page to explore business data tables and run custom queries against the data warehouse.
"""

import streamlit as st
import polars as pl
import pandas as pd
from pathlib import Path
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from enviroflow_app.elt.motherduck.md import MotherDuck

st.set_page_config(layout="wide", page_title="Business Data Explorer")

# --- Helper Functions ---


@st.cache_resource
def get_motherduck_connection():
    """Get a cached MotherDuck connection."""
    token = st.secrets["motherduck"]["token"]
    db_name = st.secrets["motherduck"]["db"]  # Use "db" key from secrets
    return MotherDuck(token=token, db_name=db_name)


@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_predefined_queries() -> List[Dict[str, Any]]:
    """Load predefined queries from the db_queries directory."""
    queries = []
    query_dir = Path("enviroflow_app/db_queries")

    if not query_dir.exists():
        return queries

    for file_path in query_dir.glob("*.sql*"):
        try:
            with open(file_path, "r") as f:
                content = f.read()

            is_template = ".j2" in file_path.suffixes or "{{" in content
            variables = (
                re.findall(r"\{\{\s*(\w+)\s*\}\}", content) if is_template else []
            )

            # Skip specific operational queries that shouldn't be run through the query explorer
            excluded_files = {
                "filter_table.sql",
                "filter_vo_quotes.sql",
                "generate_item_budget_table.sql",
                "update_quotes.sql",
                "update_item_budget_table.sql",
            }

            if file_path.name in excluded_files:
                continue

            # Skip queries with complex Jinja2 logic that our simple system can't handle
            if "{% for" in content or "{% if" in content or ".pop(" in content:
                st.warning(
                    f"Skipping {file_path.name}: Contains complex template logic not supported by this interface"
                )
                continue

            # Skip CREATE/UPDATE/DELETE statements for safety
            content_upper = content.upper().strip()
            if any(
                content_upper.startswith(stmt)
                for stmt in ["CREATE", "UPDATE", "DELETE", "DROP", "ALTER", "INSERT"]
            ):
                st.warning(
                    f"Skipping {file_path.name}: Contains data modification statements not allowed in query explorer"
                )
                continue

            queries.append(
                {
                    "name": file_path.stem.replace(".sql", "")
                    .replace("_", " ")
                    .title(),
                    "sql": content,
                    "is_template": is_template,
                    "variables": variables,
                    "type": "Pre-defined",
                }
            )
        except Exception as e:
            st.warning(f"Could not load query {file_path.name}: {e}")

    return queries


def execute_query_with_template(
    md: MotherDuck, query: str, template_vars: Optional[Dict[str, Any]] = None
) -> pl.DataFrame:
    """Execute a SQL query, handling Jinja2 templates if needed."""
    final_query = query

    if template_vars:
        try:
            from jinja2 import Template

            template = Template(query)
            final_query = template.render(template_vars)
        except Exception as e:
            raise Exception(f"Template rendering error: {e}")

    try:
        # Execute the query using the MotherDuck connection
        result = md.conn.query(final_query).pl()
        return result
    except Exception as e:
        raise Exception(f"Query execution error: {e}")


def get_business_tables() -> Dict[str, Dict[str, str]]:
    """Get predefined business data tables with user-friendly names and descriptions."""
    return {
        "Trello Cards": {
            "table": "job_cards",
            "description": "Individual job records with details, status, and progress tracking",
        },
        "Jobs": {
            "table": "jobs_for_analytics",
            "description": "Processed job data optimized for business reporting and analysis",
        },
        "Projects Raw": {
            "table": "projects",
            "description": "High-level project information and portfolio management data",
        },
        "Projects With Labour and Costs": {
            "table": "projects_for_analytics",
            "description": "Processed project data with key metrics for business insights",
        },
        "Quotes": {
            "table": "quotes",
            "description": "All customer quotations, pricing, and proposal information",
        },
        "Labour Hours": {
            "table": "labour_hours",
            "description": "Employee time tracking and labor cost allocation records",
        },
    }


def fetch_table_data(md: MotherDuck, table_name: str) -> pl.DataFrame:
    """Fetch all data from a specified table."""
    try:
        query = f"SELECT * FROM {table_name}"  # No limit - fetch all data
        result = md.conn.query(query).pl()
        return result
    except Exception as e:
        raise Exception(f"Failed to fetch data from {table_name}: {e}")


def display_data_results(
    result_df: pl.DataFrame, title: str, description: str, file_prefix: str
):
    """Unified function to display data results with statistics and download options."""
    if len(result_df) > 0:
        # Format date columns to show only ISO date (YYYY-MM-DD) without time
        formatted_df = result_df.clone()
        for col in formatted_df.columns:
            dtype = str(formatted_df[col].dtype)
            # Check if column contains datetime data
            if "datetime" in dtype.lower() or "timestamp" in dtype.lower():
                try:
                    # Convert datetime to date string format (YYYY-MM-DD)
                    formatted_df = formatted_df.with_columns(
                        pl.col(col).dt.strftime("%Y-%m-%d").alias(col)
                    )
                except Exception:
                    # If formatting fails, leave the column as is
                    pass

        # Store data in session state for PyGWalker mode
        st.session_state.current_data = formatted_df
        st.session_state.current_title = title
        st.session_state.current_description = description
        st.session_state.current_prefix = file_prefix

        # Display title and description
        st.subheader(f"📋 {title}")
        st.markdown(f"*{description}*")

        # Dive Deeper button
        st.button(
            "🔬 Dive Deeper",
            type="secondary",
            on_click=change_status,
            args=("pygwalker",),
        )

        # Default: Show standard dataframe editor
        df_pandas = formatted_df.to_pandas()
        st.data_editor(df_pandas, use_container_width=True, num_rows="dynamic")

        # Show summary statistics (collapsed by default)
        with st.expander("📊 Data Summary", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Records", f"{len(formatted_df):,}")

            with col2:
                st.metric("Fields", len(formatted_df.columns))

            with col3:
                # Calculate memory usage (approximate)
                memory_mb = formatted_df.estimated_size("mb")
                st.metric("Est. Size", f"{memory_mb:.2f} MB")

            with col4:
                # Show data types variety
                unique_types = len(set(str(dtype) for dtype in formatted_df.dtypes))
                st.metric("Data Types", unique_types)

            # Column information with statistics
            st.markdown("**Field Information:**")
            col_info = []
            for col in formatted_df.columns:
                dtype = str(formatted_df[col].dtype)
                null_count = formatted_df[col].null_count()
                null_pct = (
                    (null_count / len(formatted_df)) * 100
                    if len(formatted_df) > 0
                    else 0
                )

                # Calculate unique values
                try:
                    unique_count = formatted_df[col].n_unique()
                except Exception:
                    unique_count = "N/A"

                # Calculate median for numeric columns
                median_val = "N/A"
                if dtype in [
                    "Int64",
                    "Float64",
                    "Int32",
                    "Float32",
                    "Int16",
                    "Int8",
                ]:
                    try:
                        median_val = f"{formatted_df[col].median():.2f}"
                    except Exception:
                        median_val = "N/A"

                # Calculate mode (most frequent value)
                mode_val = "N/A"
                try:
                    # Get mode using value_counts
                    value_counts = formatted_df[col].value_counts()
                    if len(value_counts) > 0:
                        mode_val = str(value_counts.index[0])
                        # Truncate if too long
                        if len(mode_val) > 20:
                            mode_val = mode_val[:17] + "..."
                except Exception:
                    mode_val = "N/A"

                col_info.append(
                    {
                        "Field": col,
                        "Type": dtype,
                        "Unique": unique_count,
                        "Missing": null_count,
                        "Missing %": f"{null_pct:.1f}%",
                        "Median": median_val,
                        "Most Common": mode_val,
                    }
                )

            # Display column info as a small table
            col_df = pd.DataFrame(col_info)
            st.dataframe(col_df, width="content")
    else:
        st.info("Data retrieved successfully but contains no records.")


def display_pygwalker_view():
    """Display PyGWalker-only view using stored session data."""
    if st.session_state.current_data is None:
        st.error("No data available for visualization")
        return

    try:
        formatted_df = st.session_state.current_data
        file_prefix = st.session_state.current_prefix

        # Handle potential complex data types that can cause unhashable errors
        clean_df = formatted_df.clone()

        # Convert any complex data types to strings to avoid unhashable errors
        for col in clean_df.columns:
            try:
                # Check if column contains complex unhashable data types
                sample_val = clean_df[col].drop_nulls().head(1).to_list()
                if sample_val:
                    sample_item = sample_val[0]
                    sample_type = type(sample_item)
                    # Check for unhashable types: list, tuple, dict, set, numpy arrays, etc.
                    is_unhashable = (
                        sample_type in (list, tuple, dict, set)
                        or hasattr(sample_item, "__array__")
                        or str(sample_type).startswith("<class 'numpy.")
                        or hasattr(
                            sample_item, "dtype"
                        )  # numpy arrays have dtype attribute
                    )

                    if is_unhashable:
                        # Convert complex data types to string representation
                        clean_df = clean_df.with_columns(
                            pl.col(col)
                            .map_elements(
                                lambda x: str(x) if x is not None else None,
                                return_dtype=pl.Utf8,
                            )
                            .alias(col)
                        )
            except Exception:
                # If we can't process this column, leave it as is
                pass

        # Convert to pandas for PyGWalker
        df_for_pygwalker = clean_df.to_pandas()

        # Create PyGWalker configuration directory if it doesn't exist
        config_dir = Path("enviroflow_app/pages/pygwalker_confs")
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create config file path based on the file prefix
        config_file = config_dir / f"{file_prefix}.json"

        # Import PyGWalker only when needed
        from pygwalker.api.streamlit import StreamlitRenderer

        # PyGWalker data explorer with state saving - this preserves user's work
        pyg_app = StreamlitRenderer(
            df_for_pygwalker,
            spec=str(config_file),
            spec_io_mode="rw",
            appearance="light",
        )
        pyg_app.explorer()

    except Exception as e:
        st.error(f"Error creating interactive visualization: {e}")
        st.info("Please go back to the data explorer and try again.")

        # Show summary statistics (collapsed by default)
        with st.expander("📊 Data Summary", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Records", f"{len(formatted_df):,}")

            with col2:
                st.metric("Fields", len(formatted_df.columns))

            with col3:
                # Calculate memory usage (approximate)
                memory_mb = formatted_df.estimated_size("mb")
                st.metric("Est. Size", f"{memory_mb:.2f} MB")

            with col4:
                # Show data types variety
                unique_types = len(set(str(dtype) for dtype in formatted_df.dtypes))
                st.metric("Data Types", unique_types)

            # Column information with statistics
            st.markdown("**Field Information:**")
            col_info = []
            for col in formatted_df.columns:
                dtype = str(formatted_df[col].dtype)
                null_count = formatted_df[col].null_count()
                null_pct = (
                    (null_count / len(formatted_df)) * 100
                    if len(formatted_df) > 0
                    else 0
                )

                # Calculate unique values
                try:
                    unique_count = formatted_df[col].n_unique()
                except Exception:
                    unique_count = "N/A"

                # Calculate median for numeric columns
                median_val = "N/A"
                if dtype in [
                    "Int64",
                    "Float64",
                    "Int32",
                    "Float32",
                    "Int16",
                    "Int8",
                ]:
                    try:
                        median_val = f"{formatted_df[col].median():.2f}"
                    except Exception:
                        median_val = "N/A"

                # Calculate mode (most frequent value)
                mode_val = "N/A"
                try:
                    # Get mode using value_counts
                    value_counts = formatted_df[col].value_counts()
                    if len(value_counts) > 0:
                        mode_val = str(value_counts.index[0])
                        # Truncate if too long
                        if len(mode_val) > 20:
                            mode_val = mode_val[:17] + "..."
                except Exception:
                    mode_val = "N/A"

                col_info.append(
                    {
                        "Field": col,
                        "Type": dtype,
                        "Unique": unique_count,
                        "Missing": null_count,
                        "Missing %": f"{null_pct:.1f}%",
                        "Median": median_val,
                        "Most Common": mode_val,
                    }
                )

            # Display column info as a small table
            col_df = pd.DataFrame(col_info)
            st.dataframe(col_df, width="content")
    else:
        st.info("Data retrieved successfully but contains no records.")


# --- Main Page Logic ---

# Initialize connection
try:
    md = get_motherduck_connection()
except Exception as e:
    st.error(f"Failed to connect to MotherDuck: {e}")
    st.stop()

# Initialize session state for view mode switching
if "status" not in st.session_state:
    st.session_state.status = None
if "action" not in st.session_state:
    st.session_state.action = None
if "current_data" not in st.session_state:
    st.session_state.current_data = None
if "current_title" not in st.session_state:
    st.session_state.current_title = ""
if "current_description" not in st.session_state:
    st.session_state.current_description = ""
if "current_prefix" not in st.session_state:
    st.session_state.current_prefix = ""


def change_status(new_status: str):
    """Helper function to change the page status."""
    st.session_state.status = new_status


def handle_view_table():
    """Handle viewing a business table with state management."""
    st.session_state.action = "view_table"
    st.session_state.status = "main"


def handle_run_query():
    """Handle running a business query with state management."""
    st.session_state.action = "run_query"
    st.session_state.status = "main"


# --- Sidebar Controls ---
with st.sidebar:
    st.title("� Data Explorer Controls")

    business_tables = get_business_tables()
    queries = load_predefined_queries()

    if not queries:
        st.error("No queries found in db_queries directory")
        st.stop()

    # Business Data Tables Section
    st.subheader("📊 Business Data Tables")
    st.markdown("Quick access to key business data:")

    selected_business_table = st.selectbox(
        "Select Business Data",
        options=[""] + list(business_tables.keys()),
        help="Select a business data table to view its contents directly.",
    )

    st.button("📋 View Table Data", type="primary", on_click=handle_view_table)

    st.markdown("---")

    # Business Queries Section
    st.subheader("⚙️ Business Queries")
    st.markdown("Pre-built queries that business has used in the past:")

    query_options = {q["name"]: q for q in queries}
    selected_query_name = st.selectbox(
        "Select Business Query",
        options=list(query_options.keys()),
        help="Select a useful business query that has been used in the past.",
    )

    selected_query = query_options.get(selected_query_name)

    # Handle template variables if the query is a Jinja2 template
    template_vars = {}
    if selected_query and selected_query["is_template"]:
        st.markdown("---")
        st.subheader("Template Variables")
        for var in selected_query["variables"]:
            if "date" in var.lower():
                template_vars[var] = st.date_input(
                    f"Enter value for `{var}`", value=datetime.now().date()
                )
            else:
                template_vars[var] = st.text_input(f"Enter value for `{var}`")

    # Show query details in sidebar
    if selected_query:
        with st.expander("View Query SQL", expanded=False):
            st.code(selected_query["sql"], language="sql")

    # Run query button
    st.button("▶️ Run Business Query", type="primary", on_click=handle_run_query)

# --- Main Content Area ---
# Create main container for content switching
main_container = st.empty()

# Status-based navigation
if st.session_state.status == "pygwalker":
    # PyGWalker mode
    with main_container.container():
        # Prominent back button at the top
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.button(
                "⬅️ Back to Data Explorer",
                type="primary",
                use_container_width=True,
                on_click=change_status,
                args=("main",),
            )

        st.title(f"🔬 {st.session_state.current_title}")
        st.markdown(f"*{st.session_state.current_description}*")
        display_pygwalker_view()
else:
    # Default main explorer mode
    with main_container.container():
        st.title("� Data Explorer")

        # Handle business table viewing
        if st.session_state.action == "view_table" and selected_business_table:
            with st.spinner(f"Loading {selected_business_table.lower()} data..."):
                try:
                    table_name = business_tables[selected_business_table]["table"]
                    result_df = fetch_table_data(md, table_name)

                    st.success(
                        f"Successfully loaded {selected_business_table}! Showing all {len(result_df)} records."
                    )

                    # Use unified display function
                    display_data_results(
                        result_df=result_df,
                        title=f"{selected_business_table} Data",
                        description=business_tables[selected_business_table][
                            "description"
                        ],
                        file_prefix=selected_business_table.replace(" ", "_").lower(),
                    )

                    # Reset action after successful processing
                    st.session_state.action = None

                except Exception as e:
                    st.error(
                        f"Failed to load {selected_business_table.lower()} data: {str(e)}"
                    )
                    st.session_state.action = None  # Reset action on error too

        elif st.session_state.action == "view_table" and not selected_business_table:
            st.warning("Please select a business data table first.")
            st.session_state.action = None  # Reset action

        # Handle advanced query execution
        if st.session_state.action == "run_query" and selected_query:
            with st.spinner(f"Executing {selected_query['name'].lower()} query..."):
                try:
                    result_df = execute_query_with_template(
                        md, selected_query["sql"], template_vars
                    )

                    # Show template info if applicable
                    template_info = ""
                    if selected_query["is_template"]:
                        template_info = f" This analysis used the following parameters: {', '.join(selected_query['variables'])}"

                    st.success(
                        f"Business query '{selected_query['name']}' executed successfully! Retrieved {len(result_df)} rows.{template_info}"
                    )

                    # Use unified display function
                    query_description = (
                        f"Results from business query: {selected_query['name']}"
                    )
                    if selected_query["is_template"]:
                        query_description += f". Parameters used: {', '.join([f'{k}={v}' for k, v in template_vars.items()])}"

                    display_data_results(
                        result_df=result_df,
                        title=f"Query Results: {selected_query['name']}",
                        description=query_description,
                        file_prefix=selected_query_name.replace(" ", "_").lower(),
                    )

                    # Reset action after successful processing
                    st.session_state.action = None

                except Exception as e:
                    st.error(f"Business query execution failed: {str(e)}")
                    st.session_state.action = None  # Reset action on error too

        elif st.session_state.action == "run_query" and not selected_query:
            st.warning("Please select a business query first.")
            st.session_state.action = None  # Reset action

        # Show helpful getting started information when no action is taken
        if st.session_state.action is None:
            st.info(
                "👈 Use the sidebar to view business data or run useful business queries."
            )

            # Show some helpful getting started information
            st.markdown("### Getting Started")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                **📋 Business Data Tables:**
                - Select a business data table from the dropdown
                - Click "View Table Data" to see all the information
                - Use the data editor to explore the data
                """)

            with col2:
                st.markdown("""
                **⚙️ Business Queries:**
                - Choose from useful queries the business has used before
                - Fill in any required information (if needed)
                - Click the "Dive Deeper" button for advanced analysis
                - Run reports and get insights
                """)
