# Enviroflow App

Enviroflow App is a Streamlit-based business intelligence application for a drainage/construction company. It implements an ELT (Extract-Load-Transform) pipeline that integrates data from Trello, Xero, Float, and Google Sheets into MotherDuck (cloud DuckDB) for project performance analysis.

## Key Features

-   **Interactive Dashboard**: A Streamlit application for visualizing project performance, financial metrics, and operational data.
-   **Modular ELT Pipeline**: A modern, DAG-based CLI built with Typer and Rich for robust and maintainable data orchestration.
-   **Automated Data Sync**: A GitHub Actions workflow that automatically syncs data from Trello and other sources on an hourly schedule.
-   **Centralized Data Warehouse**: Uses MotherDuck to store all business data, providing a single source of truth.
-   **Code Generation**: Includes tools to automatically generate subcontractor agreements.

## Technology Stack

-   **Backend**: Python 3.10
-   **Frontend**: Streamlit
-   **CLI**: Typer, Rich
-   **Data Processing**: Polars, Pandas
-   **Database**: MotherDuck (Cloud DuckDB)
-   **Dependency Management**: Poetry
-   **CI/CD**: GitHub Actions

## Project Documentation

For a complete overview of the project architecture, development patterns, and pipeline specifications, please see the [`/docs`](./docs) directory.

-   [**`docs/dev_notes/00_Project_Overview.md`**](./docs/dev_notes/00_Project_Overview.md)
-   [**`docs/dev_notes/01_Architecture_And_Data_Flow.md`**](./docs/dev_notes/01_Architecture_And_Data_Flow.md)
-   [**`docs/dev_plan/01_Tasks_And_Roadmap.md`**](./docs/dev_plan/01_Tasks_And_Roadmap.md)

## Getting Started

### Prerequisites

-   Python 3.10+
-   [Poetry](https://python-poetry.org/) for dependency management.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Enviroflow_App
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```
    This will create a virtual environment inside the project directory (`.venv`).

3.  **Configure Secrets:**
    -   Obtain the `secrets.toml` file.
    -   Place it in the `.streamlit` directory: `.streamlit/secrets.toml`.
    -   This file contains necessary API keys for Trello, MotherDuck, etc.

4.  **Activate the virtual environment:**
    ```bash
    poetry shell
    ```

### Running the Application

-   **Run the Streamlit App:**
    ```bash
    streamlit run enviroflow_app/🏠_Home.py
    ```

-   **Run the CLI Pipeline:**
    ```bash
    python -m enviroflow_app.cli.main --help
    ```

## Data Pipeline Overview

The project uses a modern, production-ready ELT pipeline:

**CLI Pipeline (Production)**:
-   **Location**: `enviroflow_app/cli/`
-   **Architecture**: Modern, DAG-based system with 9 orchestrated tasks
-   **Execution**: Automated 3x daily via GitHub Actions (10am, 1pm, 6pm NZST, Mon-Fri)
-   **Data Sources**:
    - Trello API (job cards and projects)
    - Float API (labour hours and resources)
    - Google Sheets P&L (13,717+ cost records, 30,996+ sales records)
    - Legacy static files (fallback support)
-   **Data Destination**: MotherDuck cloud database with accurate output messaging
-   **Usage**: `python -m enviroflow_app.cli.main run-all`
-   **Status**: ✅ **Production Ready** - Processes 70M+ project value data

**Legacy System**:
-   ⚠️ **Deprecated** - `scripts/sync_data.py` and `.github/workflows/actions.yml` have been replaced by the CLI pipeline

## Development

### Code Quality

-   **Linting**: Use `ruff` for linting and auto-fixing.
    ```bash
    ruff check . --fix
    ```
-   **Type Checking**: Use `basedpyright` for static type checking.
    ```bash
    basedpyright .
    ```
-   **Formatting**: Use `black` for consistent code formatting.

For detailed development patterns and best practices, see [`docs/dev_notes/03_Development_Patterns.md`](./docs/dev_notes/03_Development_Patterns.md).
