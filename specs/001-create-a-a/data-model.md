# Data Model: Streamlit Data Management Interface

This document outlines the data access patterns and business table structures for the Streamlit Data Management Interface feature.

## 1. Business Data Tables (MotherDuck)

The interface provides access to existing business data tables in MotherDuck. No new tables are created for this feature.

### Available Business Tables

- **`job_cards`**: Individual job records with details, status, and progress tracking
- **`jobs_for_analytics`**: Processed job data optimized for business reporting
- **`projects`**: High-level project information and portfolio management data
- **`projects_for_analytics`**: Processed project data with key metrics for business insights
- **`quotes`**: All customer quotations, pricing, and proposal information
- **`labour_hours`**: Employee time tracking and labor cost allocation records

### Data Access Patterns

All data access is read-only through the MotherDuck connection. The interface uses:

- **Polars DataFrames** for data processing and manipulation
- **Cached connections** with `@st.cache_resource` for performance
- **Schema caching** with `@st.cache_resource(ttl=3600)` for metadata
- **Query result caching** with `@st.cache_data` for repeated queries

## 2. Predefined Query Structure

The Data Explorer loads predefined SQL queries from the `enviroflow_app/db_queries/` directory.

### Query Definition Format

```python
QueryDefinition = {
    "name": str,                    # User-friendly display name
    "sql": str,                     # SQL query or Jinja2 template
    "is_template": bool,            # Whether query contains {{ variables }}
    "variables": List[str],         # List of template variable names
    "type": str                     # Always "Pre-defined" for this implementation
}
```

### Template Variable Support

- Uses Jinja2 templating with `{{ variable_name }}` syntax
- Variables are extracted using regex: `r"\{\{\s*(\w+)\s*\}\}"`
- Template rendering happens at execution time with user-provided values

## 3. Session State Management

The Streamlit interface uses session state for:

- **Connection caching**: `ss.db_conn` for MotherDuck connection
- **Data caching**: `ss.available_dataframes` for loaded table data
- **Execution state**: `ss.execution_running`, `ss.execution_log` for ELT pipeline feedback
- **Query results**: `ss.pipeline_results` for execution history

## 4. Data Processing Flow

### ELT Pipeline Page
1. User selects pipeline configuration (type, destination, validation)
2. Individual operations or full pipeline execution
3. Real-time progress feedback through session state
4. Results stored in session state for exploration

### Data Explorer Page
1. User browses available business tables
2. Table data loaded and cached in session state
3. PyGWalker integration for interactive exploration
4. Predefined queries executed with optional template variables
5. Results displayed in interactive table with CSV export

## 5. Error Handling

- **Connection errors**: Displayed as user-friendly messages
- **Query execution errors**: Caught and displayed with context
- **Template rendering errors**: Validation before execution
- **Schema access errors**: Graceful fallback with available information

This data model supports the business-focused data management interface without requiring database schema changes.
