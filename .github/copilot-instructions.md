# AI Agent Instructions for the Enviroflow_App

This document p- **update notes after each milestone** update the relevant notes to reflect changes after we've agreed that we have hit a milestone. It is critical to keep the project documentation (`docs/dev_plan/*.md`) consistent and up-to-date with the latest developments. The `03_Migration_Plan.md` should be treated as the single source of truth for task status, and other documents must be aligned with it after each milestone.
- **Ask Questions Sequentially**: If you need to ask multiple questions, ask them one by one and wait for a response to each before asking the next.
- **Pause When Uncertain**: If you encounter a problem where the solution isn't clear or if you have multiple paths to explore, pause, explain the situation, and ask for guidance.
- **clean up after yourself** remove temporary files created to figure out how to solve a problem, apply Occam's razor with file creation. merge small files into larger ones if it makes sense.des essential context for working on the Enviroflow_App codebase. The primary goal is to migrate the project's data pipeline from a legacy script into a modern, modular CLI framework.

## 1. Project Purpose & Architecture

The Enviroflow_App is a business intelligence application built with Streamlit. It features an ELT pipeline to integrate data from sources like Trello and Xero into a MotherDuck data warehouse for project performance analysis. The key architectural feature is the ongoing migration from a legacy data pipeline to a modern one.

## 2. Understand the Pipeline Migration (Work in Progress)

The project is currently migrating its data pipeline from a legacy script-based system to a modern, modular CLI. Understanding both parts is key to contributing.

**a) The Legacy System (Being Replaced)**
- **What it is:** The old pipeline that currently handles production data.
- **How it works:** A GitHub Actions workflow (`.github/workflows/actions.yml`) runs `scripts/sync_data.py`. This script fetches data and commits updated Parquet/CSV files back into the `/pnl_data` and `/Data` directories.
- **Key takeaway:** For now, the production Streamlit app reads its data from these version-controlled files, not a live database.

**b) The New CLI Pipeline (The Goal)**
- **What it is:** The target architecture for all data operations.
- **Code Location:** `enviroflow_app/cli/`. It's a Typer-based CLI designed for a structured ELT process.
- **How it will work:** This new pipeline will extract data from sources, load it into MotherDuck (a cloud DuckDB instance), and run transformations there, completely replacing the old file-based system.
- **Key takeaway:** All new pipeline development must happen here. The main task is to move logic from the legacy script to the new CLI, as outlined in the migration plan.

## 3. Follow the Migration Plan

All work on the data pipeline **must** follow the official plan.
- **The Plan:** `docs/dev_plan/03_Migration_Plan.md`
- **Your Task:** Before writing any code, consult this document. It breaks down the migration into phases and specific functions. Implement the logic from the legacy `scripts/pipeline_cli.py` into the corresponding functions in the new CLI framework (`enviroflow_app/cli/operations/`).

## 4. Documentation Structure

For high-level information, refer to the `/docs` directory:
- **`docs/dev_notes/`**: Contains project overview and architecture documents.
- **`docs/dev_plan/`**: Contains the development roadmap and the critical migration plan.

## 5. Key Workflows & Commands

- **Activate Environment:**
  ```bash
  poetry shell
  ```
- **Run the Streamlit App:**
  ```bash
  streamlit run enviroflow_app/🏠_Home.py
  ```
- **Run the New CLI Pipeline:**
  ```bash
  python -m enviroflow_app.cli.main run-all
  ```
- **Linting & Type Checking:**
  ```bash
  ruff check . --fix
  basedpyright .
  ```

## 6. Code Conventions & Patterns

- **Data Processing:** Use **Polars** for all new data manipulation code. Pandas is present in legacy code but should be phased out.
- **Configuration:** App settings are in `enviroflow_app/config.py`. Secrets are managed via `.streamlit/secrets.toml`.
- **Xero Integration:** The `xero/` directory contains a standalone Flask app for a one-time, manual OAuth flow to fetch historical data. It is not a continuously running service.
- **Low-Level Rules:** For specific, file-level code quality rules (like import order, type hinting, and docstrings), refer to the existing rules in the `.cursor/rules/` directory. Do not duplicate that information here.

## 6a. Recent Changes: Data Loading GUI Simplification (2025-10-02)

**Feature Complete**: GUI simplification for `enviroflow_app/pages/6_🚚_Data_Loading_ELT.py`

**Changes Made**:
- Removed 4 tabs (Full Pipeline, Extraction Only, Transformation Only, Individual Operations) → single "Run Full Pipeline" button
- Consolidated duplicate notifications: Removed "Execution Log" section, kept only "Recent Notifications"
- Added table filtering: Table dropdown now shows only recently updated tables from most recent pipeline run
- New session state variable: `st.session_state.recently_updated_tables` (list[str]) tracks tables modified during pipeline execution
- Code reduction: 777 lines → 595 lines (23.4% reduction, 182 lines removed)

**Key Implementation Details**:
- Session state `recently_updated_tables` initialized as empty list on page load
- Cleared at start of new pipeline run in `run_full_pipeline()`
- Populated during task execution in `execute_pipeline_with_progress()` by detecting newly created tables
- Used to filter table dropdown in "Explore Results" section
- Falls back to showing all tables if no recent run exists

**Testing**:
- All integration tests passing (12/12)
- All unit tests passing (10/10)
- Manual validation scenarios defined in `specs/004-simplify-data-loading/quickstart.md`

## 7. Interaction Model

- **Summarize After Each Task:** At the end of each distinct task (like editing a file or running a command), pause, summarize the outcome, and wait for me to examine the output before proceeding.
- **update notes after each milestone** update the relevant notes to reflect changes after we've agreed that we have hit a milestone
- **Ask Questions Sequentially:** If you need to ask multiple questions, ask them one by one and wait for a response to each before asking the next.
- **Pause When Uncertain:** If you encounter a problem where the solution isn't clear or if you have multiple paths to explore, pause, explain the situation, and ask for guidance.
- **clean up after yourself** remove temporary files created to figure out how to solve a problem, apply Occam's razor with file creation. merge small files into larger ones if it makes sense.
