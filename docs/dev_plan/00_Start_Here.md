# Enviroflow App: Developer Onboarding

Welcome to the Enviroflow App project! This document is the starting point for any developer, human or AI, joining the project. It provides a high-level overview and links to more detailed documentation.

## 1. Project Overview

Enviroflow App is a business intelligence application built with Streamlit. Its core purpose is to provide project performance analysis for a drainage and construction company by integrating data from various sources into a central data warehouse.

-   **Purpose**: Centralize data, enable job costing analysis, and automate reporting.
-   **Technology Stack**:
    -   **Frontend**: Streamlit
    -   **Data Warehouse**: MotherDuck (cloud DuckDB)
    -   **Data Processing**: Polars
    -   **CLI**: Typer, Rich
    -   **Dependencies**: Poetry
    -   **CI/CD**: GitHub Actions

For more details, see the [full Project Overview](docs/dev_notes/00_Project_Overview.md).

## 2. Architecture & Production Pipeline ✅

The project has **successfully completed** its critical migration from a legacy data pipeline to a modern, production-ready system.

-   **The Legacy System (Retired)**: Previously used file-based processing with GitHub Actions committing data files back to the repository. This system has been **completely replaced**.

-   **The Modern CLI Pipeline (Production)**: The current production system is the modular CLI in `enviroflow_app/cli/`. This Typer-based application orchestrates a full ELT pipeline: extracting from multiple sources (Trello, Float, Google Sheets P&L), loading into MotherDuck cloud database, and running comprehensive transformations. **This is now the primary production system.**

**Current State**: The modern CLI pipeline is fully operational, processing 70M+ project value data with enhanced data sources including live Google Sheets integration (13,717+ cost records, 30,996+ sales records).

For a detailed breakdown, see the [Architecture and Data Flow document](docs/dev_notes/01_Architecture_And_Data_Flow.md).

## 3. Current Status & Development Focus (As of September 2025)

### ✅ **Migration Successfully Completed**

**All major migration milestones have been accomplished:**

1.  **Modular CLI Framework**: The CLI architecture in `enviroflow_app/cli/` is complete, functional, and **in production** with custom DAG orchestration.
2.  **Full Logic Migration**: All extraction and transformation logic successfully migrated from legacy scripts to new CLI operations.
3.  **P&L Integration Breakthrough**: Live Google Sheets P&L integration operational with **13,717+ cost records** and **30,996+ sales records** (vs. previous ~1,000 static records).
4.  **Production Deployment**: The `python -m enviroflow_app.cli.main run-all` command runs in production **3x daily** via GitHub Actions, processing 70M+ project value data.
5.  **Data Quality Enhancements**: Automatic deduplication (52 duplicate labour records removed), proper type conversion, and comprehensive error handling.
6.  **Legacy System Retirement**: All legacy scripts removed, old workflows disabled, modern pipeline fully operational.

### � **Current Development Focus: Feature Enhancements**

With the core migration complete, development focus has shifted to:

-   **Advanced Features**: Streamlit-based pipeline control and monitoring
-   **Dashboard Migration**: Moving P&L reports from spreadsheets to interactive Streamlit dashboards
-   **Optimization**: Performance improvements and additional data source integrations
-   **Maintenance**: Ongoing system reliability and data quality improvements

For a detailed breakdown of all migration tasks, see the **[Master Migration Plan](docs/dev_plan/03_Migration_Plan.md)**.

## 4. How to Contribute

### Environment & Setup

1.  **Activate Environment**: `poetry shell`
2.  **Run Linters**: `ruff check . --fix` and `basedpyright .`

### Key Commands

-   **Run the Streamlit App**: `streamlit run enviroflow_app/🏠_Home.py`
-   **Run the New CLI Pipeline**: `python -m enviroflow_app.cli.main run-all`
-   **Run Tests**: `pytest` or `pytest -m integration`

### Development Patterns & Reference

-   **New Logic**: All new data pipeline logic goes into `enviroflow_app/cli/operations/`.
-   **Legacy Reference**: The old `scripts/pipeline_cli.py` contains the original, working business logic. Use it as a reference.
-   **Critical Patterns**: Adhere to the established coding patterns for Polars, Typer, and circular import prevention.
-   **Detailed Guides**:
    -   [Development Patterns & Style Guide](docs/dev_notes/03_Development_Patterns.md)
    -   [New Modular CLI Reference](docs/dev_notes/04_CLI_Reference.md)

## 5. Key Documentation

-   **[Master Migration Plan](docs/dev_plan/03_Migration_Plan.md)**: The single source of truth for the pipeline migration project. Your work should align with this plan.
-   **[Data Pipeline Specification](docs/dev_notes/02_Pipeline_Specification.md)**: Detailed schemas and transformation logic for all data tables.
-   **[Google Sheets Framework Summary](docs/dev_notes/Session_Summary_Google_Sheets_Framework.md)**: Technical deep-dive into the GSheets extraction library.
-   **[Xero Integration Guide](docs/dev_notes/05_Xero_Integration_Flask_App.md)**: Explains the separate Flask app for one-time Xero data extraction.
