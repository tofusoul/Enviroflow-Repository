# CLI Reference

The Enviroflow App uses a command-line interface (CLI) to orchestrate its data pipeline. A new, modular CLI has been developed to replace the original monolithic script.

## New Modular CLI (Recommended)

The new CLI is built with Typer and Rich, providing a modern, user-friendly experience with excellent feedback. It is organized into a modular, DAG-based system.

**Status**: The CLI infrastructure is **complete and working** with enhanced extraction capabilities implemented. Key extractions (xero-costs, sales) are fully functional with MotherDuck-first architecture and comprehensive data processing.

### How to Use

All commands are run via the Python module entry point:

```bash
# Get help and see all available commands
python -m enviroflow_app.cli.main --help

# Check system version and status
python -m enviroflow_app.cli.main version
python -m enviroflow_app.cli.main status

# Run the entire pipeline (executes the DAG)
python -m enviroflow_app.cli.main run-all
```

### Command Structure

The CLI is organized into logical groups:

#### `extract`
Commands for extracting data from source systems.
```bash
python -m enviroflow_app.cli.main extract trello
python -m enviroflow_app.cli.main extract float
python -m enviroflow_app.cli.main extract xero-costs  # ✅ Enhanced with Excel date conversion
python -m enviroflow_app.cli.main extract sales       # ✅ Google Sheets P&L integration
python -m enviroflow_app.cli.main extract legacy
```

**Enhanced Extractions**:
- **xero-costs**: Comprehensive processing with Excel date conversion, proper column typing, and MotherDuck-first architecture
- **sales**: Google Sheets P&L integration with fallback mechanisms, saves as `xero_sales` table for consistency

#### `transform`
Commands for transforming raw data into structured tables.
```bash
python -m enviroflow_app.cli.main transform quotes
python -m enviroflow_app.cli.main transform jobs
python -m enviroflow_app.cli.main transform customers
python -m enviroflow_app.cli.main transform labour
python -m enviroflow_app.cli.main transform projects
python -m enviroflow_app.cli.main transform analytics
```

#### `load`
Commands for loading data to different destinations.
```bash
python -m enviroflow_app.cli.main load local-files
python -m enviroflow_app.cli.main load motherduck
```

### Verification

You can quickly verify that the CLI is working by running the following commands:
```bash
# Check that help is displayed correctly
python -m enviroflow_app.cli.main --help

# Check the status command
python -m enviroflow_app.cli.main status

# Run a sample extraction command
python -m enviroflow_app.cli.main extract trello

# Run a sample transformation command
python -m enviroflow_app.cli.main transform quotes
```

## Legacy CLI (Reference Only)

The original CLI (`scripts/pipeline_cli.py`) is a monolithic script that contains the **fully working, production-ready implementation** of the entire data pipeline. It has been preserved as a reference for its proven business logic.

**Status**: Complete and functional, but deprecated in favor of the new modular system.

### How to Use

```bash
# Run the entire legacy pipeline
python scripts/pipeline_cli.py run-all

# Run individual legacy commands
python scripts/pipeline_cli.py sync-trello
python scripts/pipeline_cli.py build-quotes
python scripts/pipeline_cli.py build-projects-analytics
```
