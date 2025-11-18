# Implementation Plan: Streamlit Data Management Interface

**Branch**: `001-create-a-a` | **Date**: 2025-09-29 | **Spec**: [specs/001-create-a-a/spec.md](./spec.md)
**Input**: Feature specification from `/home/envirodev/Projects/Enviroflow_App/specs/001-create-a-a/spec.md`

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
Create a business-focused Streamlit interface with two pages: ELT Pipeline execution with real-time feedback and Data Explorer for browsing tables and running predefined queries. The implementation focuses on simplicity and user experience, using existing MotherDuck infrastructure.

## Technical Context
**Language/Version**: Python 3.10 (Poetry managed environment)
**Primary Dependencies**: Streamlit 1.30.0+, DuckDB (MotherDuck), Polars 1.32.0+, Jinja2, PyGWalker
**Storage**: MotherDuck (cloud DuckDB) as single source of truth, read-only access
**Testing**: pytest with integration tests, focus on user workflows
**Target Platform**: Linux server deployment, web browser interface via Streamlit
**Project Type**: Single Streamlit application with modular components
**Performance Goals**: <2s query response for typical datasets, <60s timeout with user cancellation option
**Constraints**: MotherDuck-first architecture, Polars for data processing, emoji-prefixed page naming, session state caching
**Scale/Scope**: ~10 predefined queries, 6 business tables, datasets up to 100K+ rows

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **ELT Pipeline Architecture**: Interface consumes data from MotherDuck (not generating new pipeline data)
✅ **Decoupled & Reusable Pipeline Logic**: Uses existing MotherDuck connection patterns and helper functions
✅ **MotherDuck as Single Source of Truth**: All data reading from MotherDuck, no local file storage
✅ **Polars-First Data Processing**: Query results processed with Polars, converted to Pandas only for Streamlit compatibility
✅ **Test-Driven Development**: Implementation includes comprehensive testing following TDD principles
✅ **Technology Standards**: Uses approved Streamlit, MotherDuck, Polars stack
✅ **Session State Management**: Uses `enviroflow_app.st_components.pre` patterns for session initialization
✅ **Secret Management**: Uses `st.secrets["motherduck"]["token"]` for database access

## Project Structure

### Documentation (this feature)
```
specs/001-create-a-a/
├── plan.md              # This file (/plan command output)
├── spec.md              # Feature specification
├── data-model.md        # Data access patterns
├── contracts/           # Interface contracts
├── quickstart.md        # User guide
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)
```
enviroflow_app/
├── pages/
│   ├── 6_🚚_Data_Loading_ELT.py          # ELT Pipeline execution interface
│   └── 7_🔮_Data_Explorer.py             # Business data explorer
├── helpers/
│   └── query_helpers.py                  # Query execution and schema helpers
└── db_queries/                           # Predefined SQL queries
    ├── approved_jobs_list.sql
    ├── declined_jobs_list.sql
    ├── jobs_awaiting_approval.sql
    └── [additional predefined queries]
```

**Structure Decision**: Single Streamlit application with modular page components, following existing app patterns.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - PyGWalker integration patterns for business users
   - Streamlit session state management for real-time pipeline feedback
   - MotherDuck connection caching strategies
   - Business table identification and user-friendly naming

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for business data interface"
   For each technology choice:
     Task: "Find best practices for {tech} in Streamlit business applications"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all unknowns resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Business table definitions with user-friendly names
   - Predefined query structure and templating
   - Session state data structures

2. **Generate API contracts** from functional requirements:
   - Query execution interface contracts
   - Data loading operation contracts
   - Error handling contracts

3. **Generate contract tests** from contracts:
   - One test file per contract interface
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Pipeline execution workflows
   - Data exploration scenarios
   - Error handling cases

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load design docs (contracts, data model, quickstart)
- Generate tasks from Phase 1 design docs
- Each contract → contract test task [P]
- Each page → implementation task
- Each user story → integration test task

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Helper functions before pages
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 15-20 numbered, ordered tasks in tasks.md

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
| PyGWalker integration | Advanced data exploration for business users | Basic table display insufficient for complex analysis |
| Real-time pipeline feedback | User experience requirement for long-running operations | Simple progress bars insufficient for detailed feedback |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (based on existing patterns)
- [x] Phase 1: Design complete (contracts and data model defined)
- [ ] Phase 2: Task planning complete (/tasks command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v1.2.0 - See `/home/envirodev/Projects/Enviroflow_App/.specify/memory/constitution.md`*
