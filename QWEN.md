# Enviroflow App - Project Context for Qwen Code

## Project Overview

Enviroflow App is a Streamlit-based business intelligence application for a drainage/construction company. It implements an ELT (Extract-Load-Transform) pipeline that integrates data from Trello, Xero, Float, and Google Sheets into MotherDuck (cloud DuckDB) for project performance analysis.

### Key Features
- **Interactive Dashboard**: A Streamlit application for visualizing project performance, financial metrics, and operational data.
- **Modular ELT Pipeline**: A modern, DAG-based CLI built with Typer and Rich for robust and maintainable data orchestration.
- **Automated Data Sync**: A GitHub Actions workflow that automatically syncs data from Trello and other sources on an hourly schedule.
- **Centralized Data Warehouse**: Uses MotherDuck to store all business data, providing a single source of truth.
- **Code Generation**: Includes tools to automatically generate subcontractor agreements.

### Technology Stack
- **Backend**: Python 3.10
- **Frontend**: Streamlit
- **CLI**: Typer, Rich
- **Data Processing**: Polars, Pandas
- **Database**: MotherDuck (Cloud DuckDB)
- **Dependency Management**: Poetry
- **CI/CD**: GitHub Actions

## Project Structure

```
Enviroflow_App/
├── .streamlit/                 # Streamlit configuration and secrets
├── Data/                       # Data storage directory
│   ├── cli_pipeline_data/      # New CLI pipeline data
│   ├── derived/                # Derived tables
│   ├── trello_data/            # Trello data exports
│   └── ...                     # Other data sources
├── docs/                       # Project documentation
│   ├── dev_notes/              # Development notes and patterns
│   └── dev_plan/               # Development roadmap
├── enviroflow_app/             # Main application package
│   ├── 🏠_Home.py             # Main Streamlit app entry point
│   ├── cli/                    # New modular CLI pipeline
│   │   ├── commands/           # CLI command modules
│   │   ├── dag/                # DAG orchestration engine
│   │   ├── operations/         # Data operations
│   │   └── main.py             # Main CLI entry point
│   ├── elt/                    # Extract, Load, Transform components
│   │   ├── motherduck/         # MotherDuck database integration
│   │   ├── trello/             # Trello API integration
│   │   └── transform/          # Data transformation modules
│   ├── model/                  # Core data models (Project, Job, Quote)
│   ├── pages/                  # Streamlit application pages
│   ├── st_components/          # Reusable Streamlit components
│   └── config.py               # Application configuration
├── legacy/                     # Legacy code (to be deprecated)
├── scripts/                    # Utility scripts
│   └── sync_data.py            # Legacy data sync script
└── tests/                      # Test files
```

## Core Data Models

The application revolves around three key data models:

1. **Project**: Collection of Jobs that share attributes (often shared drains)
   - Contains financial information, timeline data, and customer details
   - Tracks labor costs, supplier costs, and profitability metrics

2. **Job**: Individual work orders/sites managed through Trello
   - Contains details like location, customer information, and job status
   - Linked to quotes and variation quotes

3. **Quote**: Financial quote information from Xero/Simpro
   - Contains line items, quantities, and pricing
   - Can be categorized as original quotes or variation quotes

## Data Pipeline Architecture

The project contains two parallel data pipeline systems:

### 1. New Modular CLI (Recommended for Development)
- Located in `enviroflow_app/cli/`
- A modern, DAG-based system for extracting, transforming, and validating data
- Current Status: The architecture is complete, but the core data processing functions are stubs. The next major development task is to implement the logic from the legacy script here.
- Usage: `python -m enviroflow_app.cli.main run-all`

### 2. Legacy Automated Sync (Current Production)
- Driven by `scripts/sync_data.py`
- This script is executed hourly by the GitHub Actions workflow in `.github/workflows/actions.yml`
- It fetches data from Trello, generates CSVs, derives new tables, and commits the updated data files back to the repository
- This ensures the data in the `Data/` directory is kept up-to-date automatically

## Development Workflow

### Environment Setup
1. **Install Dependencies**: Use Poetry to install and manage dependencies.
   ```bash
   poetry install
   ```
2. **Activate Virtual Environment**:
   ```bash
   poetry shell
   ```

### Running the Application
- **Run the Streamlit App**:
  ```bash
  streamlit run enviroflow_app/🏠_Home.py
  ```

- **Run the CLI Pipeline**:
  ```bash
  python -m enviroflow_app.cli.main --help
  ```

### Code Quality
- **Linting**: Use `ruff` for linting and auto-fixing.
  ```bash
  ruff check .
  ruff check . --fix
  ```
- **Type Checking**: Use `basedpyright` for static type checking.
  ```bash
  basedpyright .
  ```
- **Formatting**: Use `black` for consistent code formatting.

## Critical Implementation Patterns

### 1. Polars API Compatibility (v1.32.0+)
- Use `.map_elements()`, not `.apply()`
- Use `.group_by()`, not `.groupby()`
- Use `pl.String`, not `pl.Utf8`

### 2. Circular Import Prevention
Use function-level imports within `@cached_property` methods in the data models to prevent circular dependencies between the `model` and `elt/transform` modules.

### 3. Typer and Rich Integration
Initialize all Typer applications with `rich_markup_mode=None` to avoid a known bug in the Typer/Rich integration.

## Database Operations
- Use the `enviroflow_app/elt/motherduck/md.py` wrapper for all database interactions
- Use `conn.get_table("table_name")` to retrieve data as a Polars DataFrame
- Use `conn.save_table("table_name", df)` to save a Polars DataFrame to the database

## Secrets Management
The application requires a `.streamlit/secrets.toml` file for API credentials. This file should contain:
```toml
[motherduck]
token = "your-motherduck-token"

[trello]
api_key = "your-trello-api-key"
api_token = "your-trello-api-token"
```

## Project Roadmap

### Phase 1: Foundational Refactoring & P&L Integration (Completed)
- Modular CLI Architecture
- Full Logic Migration
- Google Sheets Framework
- P&L Integration & Data Validation

### Phase 2: Production Cutover (Current Priority)
- Update GitHub Actions to use the new CLI
- Decommission Legacy Data Sync

### Phase 3: Deprecation & Cleanup (Up Next)
- Deprecate Legacy Scripts
- Finalize Documentation

### Phase 4: Future Enhancements (Future)
- Streamlit-based Pipeline Control
- P&L Reports Dashboard

## Useful Commands

### CLI Pipeline Commands
```bash
# Run the complete ELT pipeline
python -m enviroflow_app.cli.main run-all

# Show pipeline status
python -m enviroflow_app.cli.main status

# Run validation checks
python -m enviroflow_app.cli.main validate

# Show DAG structure
python -m enviroflow_app.cli.main dag-info

# Show version information
python -m enviroflow_app.cli.main version
```

### Development Commands
```bash
# Install dependencies
poetry install

# Run the Streamlit app
streamlit run enviroflow_app/🏠_Home.py

# Run tests
pytest

# Linting
ruff check .

# Type checking
basedpyright .

# Formatting
black .
```