<!--
Sync Impact Report: v1.2.0
- Version change: 1.1.0 → 1.2.0
- Modified principles: None
- Added sections: VI. Simplicity-First Development
- Removed sections: None
- Templates requiring updates:
  ✅ No updates needed. Templates align with simplicity principle.
- Follow-up TODOs: None
-->

# Enviroflow App Constitution

## Core Principles

### I. ELT Pipeline Architecture
All data processing MUST follow the Extract-Load-Transform pattern with clear separation of concerns. Raw data is extracted from sources (Trello, Float, Google Sheets), loaded unchanged into MotherDuck, then transformed using SQL and Polars. This ensures data integrity, enables reprocessing, and maintains a clear audit trail.

**Rationale**: This pattern provides data integrity, enables reprocessing if transformations change, and maintains clear separation between raw and processed data.

### II. Decoupled & Reusable Pipeline Logic
All core data processing logic (extraction, transformation functions, and DAGs) MUST be implemented in a modular, decoupled manner. This logic must be agnostic to the execution context, enabling its use by multiple interfaces, including the automated CLI for GitHub Actions and the interactive Streamlit GUI.

**Rationale**: Ensures that business logic is defined once and can be consistently applied across different application entry points, maximizing code reuse and maintainability.

### III. MotherDuck as Single Source of Truth
All production data MUST be stored in MotherDuck (cloud DuckDB). Local file storage is permitted only for development, debugging, or temporary operations. The Streamlit application MUST consume data from MotherDuck, not local files or legacy file-based storage.

**Rationale**: Provides centralized, scalable data warehouse with consistent access patterns and eliminates data synchronization issues.

### IV. Polars-First Data Processing
All new data manipulation code MUST use Polars. Pandas is permitted only for legacy compatibility during migrations. Complex data structures must be serialized to strings for DuckDB compatibility. Polars v1.32.0+ API patterns must be followed (`.map_elements()`, `.group_by()`, `pl.String`).

**Rationale**: Provides superior performance, memory efficiency, and better type safety compared to Pandas.

### V. Test-Driven Development (NON-NEGOTIABLE)
All new functionality MUST follow test-driven development. Tests must be written and approved before implementation. Integration tests are required for external API interactions, database operations, and data transformations. Test coverage must be maintained for all business logic.

**Rationale**: Ensures reliability for business-critical financial calculations and data processing operations.

### VI. Simplicity-First Development
All solutions MUST prioritize simplicity over complexity. When functional goals are achieved, code MUST be simplified and unnecessary complexity removed. Direct implementations are preferred over abstract frameworks. Complex solutions require explicit justification and must include a simplification roadmap.

**Rationale**: Simple code is more maintainable, debuggable, and reliable. Premature optimization and over-engineering create technical debt and increase development time.

## Technology Standards

### Approved Technology Stack
- **Frontend**: Streamlit with emoji-prefixed page ordering
- **Data Warehouse**: MotherDuck (cloud DuckDB)
- **Data Processing**: Polars (primary), Pandas (legacy only)
- **CLI**: Typer with Rich (rich_markup_mode=None to avoid bugs)
- **Dependency Management**: Poetry
- **Type Checking**: basedpyright
- **Linting**: ruff with auto-fix
- **CI/CD**: GitHub Actions with 3x daily pipeline execution

### External Integration Standards
All external API integrations (Trello, Float, Google Sheets, Xero) must include error handling, retry logic, and graceful degradation. Authentication must use secure credential management via Streamlit secrets or environment variables.

## Development Workflow

### Code Quality Gates
All code changes must pass:
- `ruff check . --fix` (linting with auto-fix)
- `basedpyright .` (type checking)
- Test suite execution with full coverage
- Integration tests for external API changes

### Circular Import Prevention
Use function-level imports within `@cached_property` methods in data models to prevent circular dependencies between `model/` and `elt/transform/` modules.

### Session State Management
Streamlit pages must initialize session state using helpers in `enviroflow_app/st_components/pre.py`. Data must be loaded into session state at page start for caching efficiency.

### Secret Management
All secrets, such as API keys and database tokens, MUST be stored in the `.streamlit/secrets.toml` file. This file should not be committed to version control. Access secrets within the application code exclusively through the `st.secrets` object (e.g., `st.secrets["database"]["password"]`). This applies to both Streamlit pages and standalone scripts.

**Note for Standalone Scripts**: A script does not need to be executed with `streamlit run` to access `st.secrets`. As long as the script imports the `streamlit` library and is run from a directory containing the `.streamlit/secrets.toml` file, `st.secrets` will be correctly populated.

### Documentation Requirements
All major changes must update relevant documentation in `docs/dev_plan/03_Migration_Plan.md`. Migration status and architectural decisions must be kept current. Development patterns and best practices must be documented in `docs/dev_notes/03_Development_Patterns.md`.

## Governance

### Amendment Process
Constitution amendments require documentation of changes, impact analysis, and approval before implementation. All amendments must include migration plans for affected code and update dependency templates.

### Compliance Verification
All code reviews must verify compliance with core principles. Violations must be justified with business rationale and documented in technical debt register. Complex implementations must demonstrate necessity and provide simplification roadmap.

### Milestone Documentation
After each major milestone, relevant documentation in `docs/dev_plan/*.md` must be updated to reflect current state. The migration plan serves as the authoritative source for task status and must be kept synchronized with actual implementation progress.

**Version**: 1.2.0 | **Ratified**: 2025-09-26 | **Last Amended**: 2025-01-12
