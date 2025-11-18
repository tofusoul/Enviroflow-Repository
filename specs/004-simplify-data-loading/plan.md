
# Implementation Plan: Simplify Data Loading ELT GUI

**Branch**: `004-simplify-data-loading` | **Date**: 2025-10-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-simplify-data-loading/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Simplify the Data Loading ELT GUI by removing unused tabs (extraction-only, transformation-only, individual operations), consolidating duplicate notification displays into a single "Recent Notifications" section, and filtering the table explorer to show only recently updated tables from the most recent pipeline run. This reduces interface clutter, eliminates confusion from duplicate information, and helps users focus on relevant results.

**Technical Approach**: Remove Streamlit tabs, consolidate notification session state, track table updates during pipeline execution, filter dropdown based on recent tables list.

## Technical Context
**Language/Version**: Python 3.10+
**Primary Dependencies**: Streamlit 1.38+, Polars 1.32+, MotherDuck (DuckDB cloud), Typer (CLI)
**Storage**: MotherDuck (cloud DuckDB) as single source of truth
**Testing**: pytest for unit/integration tests, manual UI validation
**Target Platform**: Web browser (Streamlit app)
**Project Type**: Web application (single project - Streamlit handles frontend+backend)
**Performance Goals**: <2s page load, <500ms UI updates, real-time toast notifications
**Constraints**: Session state persistence during pipeline execution, toast message timing
**Scale/Scope**: Single-page UI simplification, ~766 lines current → ~500 lines target (30% reduction)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Compliance

**✅ I. ELT Pipeline Architecture**: Not applicable - this is GUI-only changes, no pipeline logic modifications.

**✅ II. Decoupled & Reusable Pipeline Logic**: Pipeline execution logic remains untouched. Only UI presentation layer changes.

**✅ III. MotherDuck as Single Source of Truth**: Existing MotherDuck queries preserved. Table filtering happens at presentation layer using existing metadata.

**✅ IV. Polars-First Data Processing**: No new data processing. Existing Polars code unchanged.

**✅ V. Test-Driven Development**: Will create UI integration tests before implementation to validate:
- Tab removal
- Notification consolidation
- Table filtering behavior

**✅ VI. Simplicity-First Development**: **THIS IS THE GOAL!** Feature removes complexity:
- Deletes ~250 lines of unused tab code
- Consolidates duplicate notification displays
- Simplifies user decision-making
- Perfect example of simplification principle

### Verdict: **PASS** ✅
No constitutional violations. This feature exemplifies Principle VI (Simplicity-First). All other principles unaffected by GUI-only changes.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
enviroflow_app/
├── pages/
│   └── 6_🚚_Data_Loading_ELT.py        # PRIMARY FILE: GUI simplification
├── st_components/
│   └── pipeline_gui.py                 # Helper functions (notification management)
└── cli/
    └── dag/
        └── pipeline.py                  # Pipeline execution (unchanged)

tests/
├── integration/
│   └── test_data_loading_gui.py        # NEW: UI integration tests
└── unit/
    └── test_pipeline_gui_helpers.py    # NEW: Notification helper tests
```

**Structure Decision**: Single project structure (Streamlit application). This is a frontend-only change affecting one primary page file and its helper module. No backend API changes needed since Streamlit handles both UI and backend logic in the same process.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - ✅ Table tracking approach: Session state list
   - ✅ "Show all tables" toggle: NO for MVP
   - ✅ Notification consolidation: Remove Execution Log, keep Recent Notifications
   - ✅ Unused function handling: Delete extraction/transform pipeline functions

2. **Generate and dispatch research agents**:
   - ✅ Q1: How to track recently updated tables? → Session state during pipeline
   - ✅ Q2: Show all tables toggle? → NO for MVP (simplicity-first)
   - ✅ Q3: How to consolidate notifications? → Delete duplicate section
   - ✅ Q4: What happens to unused functions? → Safe to delete

3. **Consolidate findings** in `research.md` using format:
   - ✅ Decision: What was chosen
   - ✅ Rationale: Why chosen
   - ✅ Alternatives considered: What else evaluated

**Output**: ✅ research.md complete with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete ✅*

1. **Extract entities from feature spec** → `data-model.md`:
   - ✅ Entity: Recently Updated Tables List (session state)
   - ✅ Entity: Notification Entry (enhanced with persistence)
   - ✅ Removed Entity: notification_placeholder (no longer needed)
   - ✅ Validation rules for both entities
   - ✅ Data flow diagram

2. **Generate UI behavioral contracts** from functional requirements:
   - ✅ Contract 1: Control Panel Structure (single button, no tabs)
   - ✅ Contract 2: Notification Display (single section)
   - ✅ Contract 3: Table Dropdown Filter (recent tables only)
   - ✅ Contract 4: Pipeline Execution Flow (table tracking)
   - ✅ Contract 5: Toast Notification Behavior (ephemeral popups)
   - ✅ Contract 6: Preserved Functionality (unchanged features)
   - ✅ Output to `/contracts/ui-behavioral-contracts.md`

3. **Generate test specifications** from contracts:
   - ✅ Unit tests: Session state management
   - ✅ Integration tests: UI behavior validation
   - ✅ Regression tests: Preserved functionality
   - ✅ Manual validation: Quickstart scenarios

4. **Extract test scenarios** from user stories:
   - ✅ Scenario 1: UI Simplification (no tabs)
   - ✅ Scenario 2: Notification Consolidation (single display)
   - ✅ Scenario 3: Pipeline Execution (notifications work)
   - ✅ Scenario 4: Recent Tables Filter (dropdown filtering)
   - ✅ Scenario 5: Empty State Handling (no tables message)
   - ✅ Scenario 6: Notification Persistence (sidebar history)
   - ✅ Scenario 7: Notification Clearing (new run clears old)
   - ✅ Scenario 8: Retained Functionality (all features work)

5. **Update agent file incrementally** (O(1) operation):
   - ✅ Ran `.specify/scripts/bash/update-agent-context.sh copilot`
   - ✅ Added Python 3.10+ to context
   - ✅ Added Streamlit 1.38+, Polars 1.32+, MotherDuck to frameworks
   - ✅ Updated .github/copilot-instructions.md

**Output**: ✅ data-model.md, /contracts/ui-behavioral-contracts.md, quickstart.md, .github/copilot-instructions.md updated

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)

**Tasks to Generate**:

1. **Setup Tasks** (Pre-implementation):
   - T001: Create test file structure
   - T002: Add test dependencies (if needed)

2. **Test Tasks** (TDD - Before Implementation):
   - T003: [P] Unit test: `test_recently_updated_tables_initialization()`
   - T004: [P] Unit test: `test_recently_updated_tables_population()`
   - T005: [P] Unit test: `test_recently_updated_tables_cleared_on_new_run()`
   - T006: [P] Unit test: `test_notification_entry_creation()`
   - T007: [P] Unit test: `test_toast_history_max_size()`

3. **Core Implementation Tasks**:
   - T008: Remove "Extraction Only" tab and `run_extraction_pipeline()` function
   - T009: Remove "Transformation Only" tab and `run_transform_pipeline()` function
   - T010: Remove "Individual Operations" tab
   - T011: Simplify Control Panel to single button
   - T012: Remove "Execution Log" section from sidebar
   - T013: Add table tracking in `execute_pipeline_with_progress()`
   - T014: Add `recently_updated_tables` session state initialization
   - T015: Filter table dropdown to recent tables only
   - T016: Add empty state handling for table dropdown

4. **Integration Test Tasks** (After Implementation):
   - T017: Integration test: Table dropdown filtering
   - T018: Integration test: Notification consolidation
   - T019: Integration test: Control panel structure
   - T020: Manual validation: Run quickstart.md scenarios

5. **Polish Tasks**:
   - T021: Remove unused imports
   - T022: Run ruff linting and fix issues
   - T023: Run basedpyright type checking
   - T024: Update documentation (if needed)

**Ordering Strategy**:
- Tests before implementation (TDD)
- Remove code before adding new features (simplification first)
- Integration tests after implementation
- Polish at the end

**Parallel Execution Markers [P]**:
- Unit tests can run in parallel (T003-T007)
- Code removal tasks depend on each other (sequential)
- Integration tests run after all implementation (sequential)

**Estimated Output**: 24 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅
- [x] Phase 1: Design complete (/plan command) ✅
- [x] Phase 2: Task planning complete (/tasks command - tasks.md generated with 36 tasks) ✅
- [ ] Phase 3: Tasks generated (/tasks command) → **SKIPPED** (tasks.md already created in Phase 2)
- [ ] Phase 4: Implementation complete (/implement command - execute tasks.md)
- [ ] Phase 5: Validation passed (run quickstart.md scenarios)

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved ✅
- [x] Complexity deviations documented: NONE (simplification feature) ✅

**Deliverables Created**:
- [x] research.md (4 research questions answered)
- [x] data-model.md (2 session state entities defined)
- [x] contracts/ui-behavioral-contracts.md (6 UI contracts)
- [x] quickstart.md (8 validation scenarios)
- [x] tasks.md (36 tasks across 5 phases)
- [x] Agent context updated (.github/copilot-instructions.md)

---
*Based on Constitution v1.2.0 - See `/memory/constitution.md`*
