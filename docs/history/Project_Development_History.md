# Project Development History

This document provides a chronological overview of the Enviroflow App's development, capturing key milestones, strategic shifts, and lessons learned.

---

### **Phase 1: The Monolithic Script (Initial State)**

-   **Architecture**: The project began with a single, monolithic Python script (`scripts/pipeline_cli.py`) responsible for the entire ELT process.
-   **Process**: A GitHub Actions workflow executed this script, which fetched data from APIs (Trello), performed transformations, and committed the resulting CSV/Parquet files back into the Git repository.
-   **Strengths**: Simple to run, contained all logic in one place.
-   **Weaknesses**: Difficult to test, debug, and maintain. Tightly coupled logic made it brittle and hard to extend. Data being version-controlled in Git was not a scalable solution.

---

### **Phase 2: Migration to a Modular CLI (Mid-2025)**

-   **Strategic Shift**: A major decision was made to refactor the entire pipeline into a modern, modular CLI application using Typer and Rich. The goal was to improve maintainability, testability, and scalability.
-   **Milestone**: The new CLI structure was created in `enviroflow_app/cli/`, complete with a custom DAG (Directed Acyclic Graph) engine for orchestrating dependencies. The original script's logic was broken down into discrete operations (`extract`, `transform`, `load`).
-   **Lessons Learned**:
    -   **Tooling**: Encountered and solved compatibility issues between `Typer` and `Rich`, requiring the `rich_markup_mode=None` setting.
    -   **API Changes**: Adapted to breaking changes in the `Polars` library, standardizing on the modern API (e.g., `.map_elements()` over `.apply()`).
    -   **Code Structure**: Discovered the need for function-level imports within `@cached_property` methods in data models to prevent circular dependencies between data models and transformation logic.

---

### **Phase 3: First End-to-End Success & Test Automation (August 2025)**

-   **Milestone**: Achieved the first successful end-to-end run of the new (stubbed) pipeline using the `run-all` command. This validated the core architecture and DAG engine.
-   **Strategic Shift**: To prevent regressions and formalize validation, a high-level integration test (`tests/integration/test_pipeline.py`) was created. This test programmatically runs the entire pipeline, ensuring its continued functionality.
-   **Lessons Learned**:
    -   **Validation is Key**: Simple warnings (e.g., about negative quote values) can cause confusion. It's important to make validation messages highly descriptive (e.g., clarifying that negative values are expected credit notes).
    -   **Testing Hierarchy**: A top-level integration test provides a crucial safety net, but the modular design also enables more granular unit tests for individual operations, which became the next focus for testing.

---

### **Phase 4: The Google Sheets P&L Framework (August 2025)**

-   **Challenge**: The next major goal was to replace a static, version-controlled `costs.parquet` file with a live data feed from a complex Google Sheets P&L spreadsheet. This presented numerous technical hurdles.
-   **Milestone**: A comprehensive, production-ready Google Sheets framework was developed (`enviroflow_app/gsheets/`). This was a significant engineering effort that went beyond a simple client.
-   **Architecture**:
    -   An enhanced client was built to handle authentication and data fetching.
    -   A flexible, injectable parser framework was created to handle different table structures (standard tables, tables with offset headers, multiple tables on one sheet, and large paginated tables).
    -   A specialized P&L client was implemented with pre-configured parsers for all target tables.
-   **Lessons Learned**:
    -   **Real-World is Messy**: Production data sources rarely fit a perfect mold. The P&L spreadsheet had headers in non-standard rows, multiple tables on a single sheet separated by an inconsistent number of blank rows, and large tables that were truncated by the API's default pagination.
    -   **Anticipate Environment Issues**: SSL certificate validation failures in a WSL environment required building automatic detection and workarounds into the client.
    -   **Abstraction Pays Off**: Creating an abstract `TableParser` class and several concrete implementations was more work upfront but resulted in a clean, extensible, and highly testable solution for handling the varied table structures.

---

### **Phase 5: Documentation Consolidation (August 2025)**

-   **Challenge**: The project had accumulated numerous documentation files, including session summaries, handover notes, and plans, leading to confusion and a high barrier to entry for new developers.
-   **Strategic Shift**: A decision was made to consolidate all essential information into a single, authoritative onboarding guide (`docs/dev_plan/00_Start_Here.md`).
-   **Process**: All existing documentation was reviewed and synthesized. Redundant information was removed, and outdated plans were updated. The new guide provides a high-level overview and links to more detailed, specialized documents.
-   **Lessons Learned**:
    -   **Documentation is a Product**: It requires curation, refactoring, and maintenance just like code.
    -   **Single Source of Truth**: A clear "start here" document is invaluable for both human and AI developers to get up to speed quickly.
    -   **Preserve History**: While consolidating, it's useful to move detailed, narrative-style documents (like session summaries) into a dedicated `history` folder to retain the context of past decisions without cluttering the main documentation.
