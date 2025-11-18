# Implementation Plan: Data Pipeline GUI Controller

**Branch**: `002-fix-and-improve` | **Date**: October 2, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-fix-and-improve/spec.md`

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

Create a user-friendly Streamlit GUI interface that wraps the existing CLI data pipeline with a single prominent "Run Full Pipeline" button. The MVP focuses on one-click execution of the complete ELT workflow with real-time feedback (color-coded log messages), copyable results for reporting, and interactive data exploration. Individual operation buttons are deferred to future iterations, significantly reducing initial scope while delivering core value.

**Technical Approach**: Single "Run Full Pipeline" button calls `Pipeline.create_full_pipeline()` from existing CLI, streams log output to Streamlit UI with color coding, displays consolidated summary upon completion, and provides PyGWalker integration for data exploration—all reusing existing patterns from Data Explorer and Subcontract Generator pages.

**Scope Reduction**: Original spec included 15+ individual operation buttons (extract trello, extract float, transform quotes, etc.). MVP simplifies to single "Run Full Pipeline" button only. Individual operations can be added in future iteration if needed.

## Technical Context
**Language/Version**: Python 3.10+
**Primary Dependencies**: Streamlit, Polars, Typer, Rich, pygwalker (existing stack)
**Storage**: MotherDuck (cloud DuckDB) for all production data
**Testing**: pytest with integration tests for pipeline operations
**Target Platform**: Web browser via Streamlit server
**Project Type**: Single Streamlit application (existing codebase extension)
**Performance Goals**: Full pipeline execution must match CLI performance (2-5 minutes); UI must remain responsive during execution
**Constraints**: Must work within Streamlit's execution model; single user operation at a time (session-level locking)
**Scale/Scope**: Single page (~300-500 LOC for MVP), one primary button ("Run Full Pipeline"), real-time log streaming, data exploration integration

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **ELT Pipeline Architecture**: GUI wraps existing CLI operations; does not modify core ELT logic
✅ **Decoupled & Reusable Pipeline Logic**: Uses `enviroflow_app/cli/operations/` without modification
✅ **MotherDuck as Single Source of Truth**: All data operations target MotherDuck; reads from MotherDuck for exploration
✅ **Polars-First Data Processing**: Uses Polars DataFrames throughout; Pandas only for Streamlit compatibility where required
✅ **Test-Driven Development**: Will create integration tests before implementation
✅ **Simplicity-First Development**: Direct function calls to CLI operations; no new abstractions
✅ **Technology Standards**: Uses approved Streamlit, MotherDuck, Polars stack
✅ **Session State Management**: Uses `enviroflow_app.st_components.pre` patterns
✅ **Secret Management**: Uses `st.secrets` for all credentials

**No constitution violations detected. Proceed to Phase 0.**

## Project Structure

### Documentation (this feature)
```
specs/002-fix-and-improve/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
enviroflow_app/
├── pages/
│   └── 6_🚚_Data_Loading_ELT.py          # Main implementation file (to be replaced)
├── cli/
│   ├── operations/
│   │   ├── extraction_ops.py              # Existing extraction functions (reused)
│   │   ├── transform_ops.py               # Existing transform functions (reused)
│   │   └── validation_ops.py              # Existing validation functions (reused)
│   ├── dag/
│   │   └── pipeline.py                    # Pipeline orchestration (reused)
│   └── config.py                          # Pipeline configuration (reused)
├── st_components/
│   ├── pre.py                             # Session state helpers (reused)
│   └── pipeline_gui.py                    # New: Reusable GUI components for pipeline execution
└── elt/
    └── motherduck/
        └── md.py                          # MotherDuck connection (reused)

tests/
└── integration/
    └── test_pipeline_gui.py               # New: Integration tests for GUI
```

**Structure Decision**: Single Streamlit application following existing page patterns. The implementation is a single page file that wraps existing CLI operations without modifying core pipeline logic. All existing CLI infrastructure (`operations/`, `dag/`, `config.py`) is reused without changes.

## Phase 0: Outline & Research

**Status**: ✅ Complete

**Research Tasks Completed**:
1. ✅ UI Architecture Pattern - Two-column layout following existing pages
2. ✅ Real-Time Feedback Mechanism - `st.empty()` containers with streaming updates
3. ✅ Pipeline Operation Execution - Direct function calls to CLI operations
4. ✅ Execution State Management - Streamlit session state with tracking keys
5. ✅ Log Message Categorization - Emoji icons with Streamlit color helpers
6. ✅ Copyable Results Format - Markdown text with `st.code()` blocks
7. ✅ Data Table Exploration - Reuse PyGWalker from Data Explorer
8. ✅ Error Handling Strategy - Graceful degradation with clear messaging
9. ✅ Concurrency Control - Session-level locking with boolean flag
10. ✅ Progress Indication - Indeterminate spinner + live logs

**Output**: [research.md](./research.md) - All design decisions documented with rationale

**Key Findings**:
- No new dependencies required - reuse existing stack
- CLI operations already designed for import and function calls
- Session state pattern well-established in codebase
- Performance fits within Streamlit timeouts (5 min max, operations take 2-5 min)
- Security handled by existing `st.secrets` infrastructure

## Phase 1: Design & Contracts

**Status**: ✅ Complete

### Data Model
**Output**: [data-model.md](./data-model.md)

Defined:
- Session state schema (execution control, logs, results, history)
- Pipeline operation metadata structure (15+ operations cataloged)
- UI configuration (colors, icons, layout)
- Data flow for user-initiated operations, execution, and completion
- MotherDuck integration patterns
- Error handling data structures
- Testing data structures (mock fixtures)

**Key Design Points**:
- Simple session state model (no database persistence)
- Single "Run Full Pipeline" button (MVP - no individual operations)
- Full pipeline operation defined using existing `Pipeline.create_full_pipeline()`
- Read-only MotherDuck integration for exploration
- Memory management (log rotation, history pruning)

### Quickstart Guide
**Output**: [quickstart.md](./quickstart.md)

Documented:
- Setup prerequisites and credential verification
- First-time user walkthrough (step-by-step screenshots in text)
- Common workflows (daily refresh, troubleshooting, verification)
- Troubleshooting guide with solutions
- Advanced usage patterns
- Integration with other app pages
- Testing checklist for developers

### Agent Context
**Output**: Updated `.github/copilot-instructions.md`

Added feature context:
- Language: Python 3.10+
- Frameworks: Streamlit, Polars, Typer, Rich, pygwalker
- Database: MotherDuck (cloud DuckDB)
- Project type: Single Streamlit application extension

### Contracts (Not Applicable)
This feature is a UI wrapper without API contracts. The "contract" is the existing full pipeline execution signature:

```python
# Existing contract (not modified by this feature):
from enviroflow_app.cli.dag import Pipeline

# Create and execute full pipeline
engine = Pipeline.create_full_pipeline()
engine.config = config  # Pipeline configuration
results = engine.execute()  # Returns dict with operation results
```

**MVP Focus**: Single button calls `Pipeline.create_full_pipeline().execute()`. Individual operation buttons deferred to future iteration.

**Contract Tests**: Integration tests will verify GUI correctly calls the full pipeline execution.

**Re-evaluation of Constitution Check**: ✅ No violations introduced. Design remains compliant.

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate implementation tasks following TDD order for MVP scope
3. Focus on single "Run Full Pipeline" button with feedback
4. Integration tests verify GUI state management and full pipeline execution
5. Defer individual operation buttons to future iteration

**MVP Task Categories** (Priority 1):
- **Setup & Configuration** (1-2 tasks): Session state schema, pipeline config
- **UI Layout** (2 tasks): Two-column structure, single button control panel, feedback panel
- **Full Pipeline Execution** (2-3 tasks): "Run Full Pipeline" button implementation, DAG integration, result capture
- **Real-Time Feedback** (2-3 tasks): Log streaming with color coding, progress spinner, result summary display
- **Data Exploration** (1-2 tasks): Table list display, PyGWalker integration
- **Error Handling** (2 tasks): Connection errors, API failures with clear messaging
- **User Features** (1-2 tasks): Copy results button, execution status display
- **Browser UI Testing** (2 tasks): Visual verification of layout/colors, responsive design testing
- **Integration Tests** (2-3 tasks): State management, full pipeline execution, error scenarios
- **Documentation** (1 task): Inline comments, docstrings

**Future Enhancement Categories** (Priority 2 - deferred):
- Individual operation buttons (extract: trello, float, xero-costs, sales)
- Transform operation buttons (quotes, jobs, customers, add-labour, projects)
- Validation operation button
- Per-operation history and timestamps
- Dependency checking between operations
- Advanced configuration options (output destination selection)

**Ordering Strategy (MVP)**:
1. **Phase 1: Foundation**
   - Session state schema implementation
   - Pipeline configuration setup
   - UI layout structure (two columns, single button)

2. **Phase 2: Core Functionality** (depends on Phase 1)
   - "Run Full Pipeline" button implementation
   - Call to `Pipeline.create_full_pipeline().execute()`
   - Real-time log capture and streaming
   - Color-coded log display

3. **Phase 3: User Experience** (depends on Phase 2)
   - Error handling and display
   - Copy results feature
   - Data exploration (table list + PyGWalker)

4. **Phase 4: Verification** (depends on all previous)
   - Browser UI testing (visual verification)
   - Responsive design testing
   - Integration tests
   - Documentation

**Estimated Task Count**: 15-20 numbered tasks (MVP scope)

**Dependencies**:
- Sequential tasks build on previous outputs
- Integration tests depend on implementation tasks
- **Browser UI testing depends on UI layout implementation**
- No external dependencies (all within existing codebase)
- **MVP scope: No individual operation buttons, so no operation catalog or dependency checking needed**

**IMPORTANT**: Task generation is executed by the /tasks command, NOT by /plan. This section provides the approach for task breakdown.

## Complexity Tracking

**No Constitution Violations**: This section is empty because no constitutional principles are violated.

The implementation is intentionally simple:
- Wraps existing functionality without modification
- No new abstractions or frameworks
- Direct function calls to CLI operations
- Standard Streamlit patterns throughout
- Reuses all existing infrastructure

## Progress Tracking

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - approach described above)
- [ ] Phase 3: Tasks generated (/tasks command - NEXT STEP)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (no violations detected)
- [x] Post-Design Constitution Check: PASS (design maintains compliance)
- [x] All NEEDS CLARIFICATION resolved (spec was clear, no clarifications needed)
- [x] Complexity deviations documented (none - no deviations)

**Artifacts Generated**:
- [x] research.md (Phase 0)
- [x] data-model.md (Phase 1)
- [x] quickstart.md (Phase 1)
- [x] `.github/copilot-instructions.md` updated (Phase 1)
- [ ] tasks.md (Phase 2 - awaiting /tasks command)

---

## Summary for /tasks Command

When `/tasks` is executed, generate **MVP scope** tasks:

1. **Setup tasks** for session state (execution control, logs, results)
2. **UI implementation tasks** for two-column layout with single "Run Full Pipeline" button
3. **Full pipeline integration task** calling `Pipeline.create_full_pipeline().execute()`
4. **Feedback system tasks** for color-coded log streaming, progress spinner, result summary
5. **Error handling tasks** for graceful degradation with clear user messages
6. **Exploration tasks** for table list display and PyGWalker integration
7. **Copy results task** for formatted Markdown output
8. **Browser UI testing tasks** for visual verification and responsive design
9. **Integration test tasks** for state management and full pipeline execution
10. **Documentation task** for code comments

**Scope**: MVP focuses on single "Run Full Pipeline" button. Individual operation buttons (extract trello, transform quotes, etc.) are explicitly **out of scope** for initial implementation. These can be added in future iteration if needed.

Follow TDD principles where applicable. Estimated 15-20 tasks for MVP scope.

---

**Plan Complete**: Ready for `/tasks` command to generate detailed task breakdown.

*Based on Constitution v1.2.0 - See `.specify/memory/constitution.md`*
