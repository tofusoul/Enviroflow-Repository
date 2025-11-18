# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Key Development Commands

- **Activate virtual environment**: `poetry shell`
- **Install dependencies**: `poetry install`
- **Run Streamlit app**: `streamlit run enviroflow_app/🏠_Home.py`
- **Run CLI pipeline**: `python -m enviroflow_app.cli.main run-all`
- **Linting and auto-fix**: `ruff check . --fix`
- **Type checking**: `basedpyright .`
- **Run all tests**: `pytest`
- **Run a specific test file**: `pytest tests/test_specific_module.py`

## Code Style Guidelines

- **Import Order**: Standard library → Third-party → Local application imports.
- **Type Annotations**: Use modern Python syntax (e.g., `dict[str, Any]` instead of `typing.Dict[str, Any]`).
- **Data Processing**: Use Polars for new code; legacy code uses Pandas.
- **Naming Conventions**: Follow existing conventions in the module you are editing.
- **Error Handling**: Use try-except blocks for operations that can fail (e.g., API calls, file I/O).
- **Streamlit**: Assign unused component results to `_`. Page files use emoji prefixes for ordering.
- **CLI**: Use Typer with Rich for output. Follow DAG-based orchestration patterns.
- **Documentation**: Update `docs/dev_plan/03_Migration_Plan.md` after completing tasks.
