# Project Roadmap

This document outlines the high-level strategic phases for the Enviroflow App project. For a detailed, task-level breakdown, please refer to the **[Master Migration Plan](03_Migration_Plan.md)**.

---

### ✅ **Phase 1: Foundational Refactoring & P&L Integration (Completed)**

This phase focused on migrating the project from a monolithic script to a modern, maintainable, and testable architecture, culminating in the successful integration of live P&L data.

-   [x] **1.1: Modular CLI Architecture**: Replaced the legacy `scripts/pipeline_cli.py` with a modular, DAG-based CLI application in `enviroflow_app/cli/`.
-   [x] **1.2: Full Logic Migration**: Ported all core extraction and transformation logic to the new CLI framework.
-   [x] **1.3: Google Sheets Framework**: Engineered a production-ready framework (`enviroflow_app/gsheets/`) to handle complex data extraction from Google Sheets.
-   [x] **1.4: P&L Integration & Data Validation**: Successfully integrated the P&L Google Sheet, increasing cost data from ~1k to 13k+ records and validating the full end-to-end pipeline.

---

### ✅ **Phase 2: Production Cutover (Completed)**

The data pipeline was successfully deployed to production with enhanced capabilities.

-   [x] **2.1: Update GitHub Actions**: Created new production workflow `.github/workflows/cli_pipeline.yml` executing the modern CLI (`python -m enviroflow_app.cli.main run-all`) with 3x daily scheduling.
-   [x] **2.2: Decommission Legacy Data Sync**: Disabled old workflow (`.github/workflows/actions.yml.disabled`) and removed `git-auto-commit-action` as the new pipeline writes directly to MotherDuck.

---

### ✅ **Phase 3: Deprecation & Cleanup (Completed)**

Legacy components have been successfully removed and documentation modernized.

-   [x] **3.1: Deprecate Legacy Scripts**: Successfully removed `scripts/pipeline_cli.py` and `scripts/sync_data.py` after complete logic migration.
-   [x] **3.2: Finalize Documentation**: Updated `README.md` to reflect the production-ready CLI pipeline, created comprehensive session documentation, and maintained detailed migration history.

---

### 🚀 **Phase 4: Future Enhancements (Available for Development)**

With the complete migration successfully accomplished, focus can now shift to user-facing enhancements and advanced features.

-   [ ] **4.1: Streamlit-based Pipeline Control**: Integrate the `DAGEngine` into the Streamlit UI to allow for manually triggering and monitoring pipeline runs from the web app.
-   [ ] **4.2: P&L Reports Dashboard**: Migrate the financial reports currently generated in the P&L spreadsheet into a new, interactive Streamlit dashboard, using the live MotherDuck data.

### 📊 **Migration Success Summary**

**✅ Complete Legacy-to-Modern CLI Migration Accomplished:**
- **Enhanced Data Sources**: Live Google Sheets P&L with 13,717+ cost records, 30,996+ sales records
- **Production Deployment**: 3x daily automated runs via GitHub Actions with MotherDuck cloud storage
- **Data Quality**: Automatic deduplication, proper type conversion, comprehensive error handling
- **Architecture**: Modern DAG-based pipeline processing 70M+ project value data
- **Cleanup**: Legacy scripts removed, documentation modernized, codebase streamlined
