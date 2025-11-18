# Architecture and Data Flow

This document outlines the core architecture of the Enviroflow App, its key components, and the flow of data through the system.

## Core Architecture

The application is designed with a clear separation of concerns, organizing the system into distinct layers for data processing, business logic, and presentation.

### Key Components

-   **`enviroflow_app/`**: The main application package.
    -   **`🏠_Home.py`**: The primary entry point for the Streamlit application.
    -   **`cli/`**: The new modular, DAG-based command-line interface for pipeline orchestration.
    -   **`elt/`**: The core Extract, Load, and Transform components.
        -   **`motherduck/`**: A dedicated wrapper for all MotherDuck database interactions.
        -   **`trello/`**, **`gsheets/`**: Modules for integrating with external APIs.
        -   **`transform/`**: The heart of the business logic, containing all data transformation modules.
    -   **`model/`**: Contains the core business entity data models (`Project`, `Job`, `Quote`), which use `@cached_property` for efficient, on-demand calculations.
    -   **`pages/`**: Individual Streamlit pages, numbered with emoji prefixes for sidebar ordering.
    -   **`st_components/`**: Reusable Streamlit components, including session state management (`pre.py`) and UI widgets.

### Data Flow Pattern

The application follows a standard ELT (Extract-Load-Transform) pattern, which is orchestrated by the CLI pipeline:

1.  **Extract**: Raw data is pulled from source APIs (Trello, Float, etc.) and external files (Google Sheets).
2.  **Load**: The raw, unprocessed data is loaded directly into corresponding tables in MotherDuck. This ensures data integrity and provides a source for reprocessing if needed.
3.  **Transform**: SQL queries and Polars DataFrames are used to transform the raw data in MotherDuck into structured, analytics-ready tables and business objects (`Project`, `Job`).
4.  **Present**: The final, transformed data is exposed through the Streamlit application, where it is loaded into cached session state for fast, interactive use in the UI.

## Production Pipeline Architecture (September 2025)

The project now operates with a single, modern data pipeline that has replaced the legacy system:

### CLI Pipeline (Production)

-   **Trigger**: Runs automatically 3x daily via GitHub Actions workflow (`.github/workflows/cli_pipeline.yml`) at 10am, 1pm, and 6pm NZST (Mon-Fri)
-   **Orchestration**: Driven by the modular CLI (`enviroflow_app/cli/main.py`) with DAG-based task execution
-   **Process**: Full ELT pattern with enhanced data integration:
    1.  **Extract**: Fetches data from multiple sources:
        - Trello API (job cards and project data)
        - Float API (labour hours and resource tracking)
        - Google Sheets P&L (13,717+ cost records and 30,996+ sales records)
        - Legacy static files (fallback for miscellaneous data)
    2.  **Load**: Raw data loaded directly to MotherDuck cloud database ('enviroflow' database)
    3.  **Transform**: SQL and Polars transformations within MotherDuck to create analytics-ready tables
-   **Output Destination**: All data stored in MotherDuck cloud database with accurate user feedback messaging
-   **Data Volume**: Processes 70M+ project value data across 9 pipeline tasks
-   **Outcome**: Live business intelligence data available immediately in cloud database for Streamlit app consumption

### Legacy System (Deprecated)

-   **Status**: ⚠️ **DEPRECATED** - `.github/workflows/actions.yml` and `scripts/sync_data.py` are no longer used
-   **Migration Complete**: All functionality successfully migrated to CLI pipeline with enhanced capabilities

## Data Model Relationships

The business logic is built around a hierarchy of core data models.

### Core Entity Hierarchy

-   **Project**: The top-level entity, which contains one or more related **Jobs**. A project aggregates all financial and operational data from its constituent jobs.
-   **Job**: An individual unit of work, typically corresponding to a Trello card. A job can have multiple **Quotes** associated with it (e.g., an original quote and subsequent variations).
-   **Quote**: Represents a financial quote from Xero or Simpro, containing line items and pricing details.

*Note: To ensure compatibility with DuckDB, complex data structures within the models (like timelines or customer details) are serialized to strings before being saved to the database.*

### Financial Calculations

The `Project` model contains the core financial logic, with calculations chained together using cached properties:

```
// Core calculation flow in the Project model
total_quote_value  -> merged_quotes.quote_value
labour_costs_total -> labour_hours * LABOUR_RATE
supplier_costs_total -> sum(supplier_costs["Gross"])
total_costs        -> labour_costs_total + supplier_costs_total
gross_profit       -> total_quote_value - total_costs
gp_margin_pct      -> gross_profit / total_quote_value
```
