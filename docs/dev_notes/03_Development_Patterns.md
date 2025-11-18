# Development Patterns and Style Guide

This document outlines the established patterns, conventions, and best practices for developing the Enviroflow App.

## Development Workflow

### Environment Setup

1.  **Install Dependencies**: Use Poetry to install and manage dependencies.
    ```bash
    poetry install
    ```
2.  **Activate Virtual Environment**:
    ```bash
    poetry shell
    ```
3.  **Verify Dependencies**: Ensure you are using the correct versions.
    ```bash
    python -c "import typer; print('Typer:', typer.__version__)"
    # Expected: 0.12.5
    python -c "import rich; print('Rich:', rich.__version__)"
    # Expected: 13.9.4
    python -c "import polars; print('Polars:', polars.__version__)"
    # Expected: 1.32.2
    ```
4.  **Run the App**:
    ```bash
    streamlit run enviroflow_app/🏠_Home.py
    ```
5.  **Run the Pipeline**:
    ```bash
    python -m enviroflow_app.cli.main --help
    ```

### Code Quality

-   **Linting**: Use `ruff` for linting and auto-fixing.
    ```bash
    ruff check .
    ruff check . --fix
    ```
-   **Type Checking**: Use `basedpyright` for static type checking.
    ```bash
    basedpyright .
    ```
-   **Formatting**: Use `black` for consistent code formatting (configured in `pyproject.toml`).

## Critical Implementation Patterns

These are proven solutions to key technical challenges encountered during development. **Adhere to these patterns to avoid common issues.**

### 1. Polars API Compatibility (v1.32.0+)

The project uses a recent version of Polars. Ensure you use the current, non-deprecated API methods.

-   **Use `.map_elements()`**, not `.apply()`.
-   **Use `.group_by()`**, not `.groupby()`.
-   **Use `pl.String`**, not `pl.Utf8`.

```python
# CORRECT (Polars 1.32.0+)
df.with_columns(
    pl.col("A").map_elements(lambda x: process(x))
).group_by("B").agg(...)
```

### 2. Circular Import Prevention

Circular dependencies can occur between the `model` and `elt/transform` modules. To prevent this, **use function-level imports** within `@cached_property` methods in the data models.

```python
# CORRECT - Import inside the method
@cached_property
def merged_quotes(self) -> Quote | None:
    from enviroflow_app.elt.transform.from_quotes import From_Quotes_List
    return From_Quotes_List(self.quotes).merge_quotes(self.name)
```

### 3. Typer and Rich Integration

To avoid a known bug in the Typer/Rich integration, initialize all Typer applications with `rich_markup_mode=None`. Rich formatting for console output will still work correctly.

```python
# CORRECT
app = typer.Typer(rich_markup_mode=None)
```

## General Best Practices

### Session State Management

-   Always initialize the Streamlit session state using the helpers in `enviroflow_app/st_components/pre.py`.
-   Load required data into the session state at the beginning of each page script to leverage caching.

```python
from enviroflow_app.st_components import pre

pre.setup_streamlit_page()
pre.init_default_session()
pre.load_md_data_to_session_state(tables=["quotes", "job_cards"])
ss = st.session_state
```

### Database Operations

-   Use the `enviroflow_app/elt/motherduck/md.py` wrapper for all database interactions to ensure consistency.
-   Use `conn.get_table("table_name")` to retrieve data as a Polars DataFrame.
-   Use `conn.save_table("table_name", df)` to save a Polars DataFrame to the database.

### Type Safety and Linting

-   Use `cast` for dictionary configurations to satisfy the type checker (e.g., `cast("dict[str, Any]", config.APP_LOG_CONF)`).
-   Assign unused Streamlit return values to `_` to avoid linting errors (e.g., `_ = st.toggle("Dev Mode")`).
-   Follow standard import order: standard library, then third-party packages, then local application modules.

## Common Gotchas

-   **Stringified Data Structures**: Complex objects in the data models (like lists or structs) are serialized to strings before saving to DuckDB. They must be deserialized after loading.
-   **Hardcoded Constants**: Key business logic constants (e.g., `LABOUR_RATE`) are currently hardcoded in the `Project` model.
-   **Secrets Management**: The application requires a `.streamlit/secrets.toml` file for API credentials. Access them via `st.secrets["service"]["key"]`.
-   **Emoji Filenames**: Page filenames use emojis for ordering in the Streamlit sidebar. This may trigger linting warnings (N999), which is acceptable.
