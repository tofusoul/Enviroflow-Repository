# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enviroflow App is a Streamlit-based business intelligence application for a drainage/construction company. It implements an ELT (Extract-Load-Transform) pipeline that integrates data from Trello, Xero, Float, and Google Sheets into MotherDuck (cloud DuckDB) for project performance analysis.

## Key Development Commands

### Environment Setup
```bash
# Activate virtual environment
poetry shell

# Install dependencies
poetry install
```

### Running the Application
```bash
# Run Streamlit app (main entry point)
streamlit run enviroflow_app/🏠_Home.py

# Run CLI pipeline
python -m enviroflow_app.cli.main run-all
```

### Code Quality & Testing
```bash
# Linting and auto-fix
ruff check . --fix

# Type checking
basedpyright .

# Run tests
pytest

# Run specific test file
pytest tests/test_specific_module.py
```

## Architecture Overview

### Core Components

**Streamlit Application**: `enviroflow_app/🏠_Home.py` serves as the main entry point, routing to various pages in `enviroflow_app/pages/`

**Modern CLI Pipeline**: `enviroflow_app/cli/` contains the new production-ready ELT pipeline with:
- DAG-based orchestration (`cli/dag/`)
- Modular extraction commands (`cli/commands/extract.py`)
- Transformation operations (`cli/operations/transform_ops.py`)
- Loading commands (`cli/commands/load.py`)

**Data Models**: Core entities in `enviroflow_app/model/` including Project, Job, and Quote classes

**ELT Operations**: `enviroflow_app/elt/` contains data transformation logic and external service integrations

### Data Flow Architecture

The project is migrating from a legacy file-based system to a modern database-driven architecture:

**Current State**: Legacy pipeline (`.github/workflows/actions.yml` → `scripts/sync_data.py`) commits Parquet/CSV files to `/pnl_data` and `/Data` directories

**Target State**: Modern CLI pipeline extracts data from sources, loads into MotherDuck, and runs transformations in-database

**Key Data Sources**:
- Trello API (job cards and projects)
- Float API (labour hours and resources)
- Google Sheets P&L (13,717+ cost records, 30,996+ sales records)
- Xero API (financial data)

### Configuration Management

**App Configuration**: `enviroflow_app/config.py` contains API configs, logger settings, and application-wide settings

**Secrets**: `.streamlit/secrets.toml` (not in repo) contains API keys for Trello, MotherDuck, etc.

## Development Patterns

### Code Organization
- **Import Order**: Standard library → Third-party → Local application imports
- **Type Annotations**: Use modern Python syntax (`dict[str, Any]` instead of `Dict[str, Any]`)
- **Data Processing**: Use Polars for new code (legacy uses Pandas)
- **Logger Configuration**: Use `cast("dict[str, Any]", config.LOG_CONF)` pattern

### Streamlit-Specific Patterns
- Assign unused Streamlit component results to `_` (e.g., `_ = st.toggle()`)
- Page files use emoji prefixes for ordering: `5_💰_Project_Performance.py`
- Session state management through `enviroflow_app.st_components.pre`

### CLI Development
- Use Typer for CLI framework with Rich for output formatting
- Follow DAG-based pipeline orchestration patterns
- Implement validation operations in `cli/operations/validation_ops.py`

## Key Files and Directories

### Critical Files
- `enviroflow_app/🏠_Home.py` - Main Streamlit app entry point
- `enviroflow_app/cli/main.py` - Modern CLI pipeline entry point
- `enviroflow_app/config.py` - Application configuration
- `pyproject.toml` - Dependencies and tool configuration

### Important Directories
- `enviroflow_app/pages/` - Streamlit page implementations
- `enviroflow_app/cli/operations/` - CLI pipeline operations
- `enviroflow_app/elt/` - ELT transformation logic
- `enviroflow_app/model/` - Data model definitions
- `docs/dev_plan/` - Development roadmap and migration plan

## Migration Context

The project is actively migrating from legacy scripts to the modern CLI framework. All new pipeline development should follow the migration plan in `docs/dev_plan/03_Migration_Plan.md`. The legacy system (`.github/workflows/actions.yml` and `scripts/sync_data.py`) is being replaced by the CLI pipeline in `enviroflow_app/cli/`.

## Tool Configuration

### Ruff (Linter)
- Configured in `pyproject.toml`
- Select rules: `["E", "F"]`
- Ignores: `["E501", "E402"]`
- Common command: `ruff check . --fix`

### BasedPyright (Type Checker)
- Configured in `pyproject.toml`
- Multiple warnings suppressed for Streamlit compatibility
- Common command: `basedpyright .`

### Testing
- Pytest configuration in `pyproject.toml`
- Integration test markers available
- Test files should be placed in `tests/` directory

## Documentation and Progress Tracking

### Critical Documentation
Always refer to the `/docs` folder for comprehensive project context:
- **Migration Plan**: `docs/dev_plan/03_Migration_Plan.md` - Single source of truth for task status and pipeline migration progress
- **Project Overview**: `docs/dev_notes/00_Project_Overview.md` - High-level architecture and goals
- **Architecture**: `docs/dev_notes/01_Architecture_And_Data_Flow.md` - Data flow and system design
- **CLI Reference**: `docs/dev_notes/04_CLI_Reference.md` - Complete CLI command documentation
- **Development Patterns**: `docs/dev_notes/03_Development_Patterns.md` - Coding standards and best practices

### Progress Tracking Requirements
After completing any task or milestone:
1. **Update Migration Plan**: Always update `docs/dev_plan/03_Migration_Plan.md` to reflect current status
2. **Document Lessons Learned**: Add session summaries to appropriate `docs/dev_notes/Session_Summary_*.md` files
3. **Track Plan Changes**: If requirements or approaches change during development, document these changes in the relevant planning documents
4. **Maintain Consistency**: Ensure all documentation remains consistent with the actual implementation

### Context Clarification
When starting any task:
1. **Review Current Status**: Check `docs/dev_plan/03_Migration_Plan.md` for current task status
2. **Understand Dependencies**: Review architecture documents to understand system relationships
3. **Follow Established Patterns**: Refer to development patterns for code organization
4. **Update as You Go**: Document progress and lessons learned immediately after completing work

### Documentation Maintenance
- **Single Source of Truth**: Treat the migration plan as the authoritative task tracker
- **Real-time Updates**: Update documentation immediately after changes, not at the end of sessions
- **Cross-references**: Ensure all related documents reference each other appropriately
- **Version Control**: Commit documentation changes along with code changes
