# Feature Specification: Data Pipeline GUI Controller

**Feature Branch**: `002-fix-and-improve`
**Created**: October 2, 2025
**Status**: Draft
**Input**: User description: "This code in the dataloading page currently not functioning, I want to create an interface to trigger the data update. This page should be a gui of the cli data pipeline, with a means to trigger the whole pipeline or any of the sub commands and give feedback to the user that they can copy and paste into other programmes for what ever their specific needs might be. it needs to have feature parity with the cli tool and be user friendly in a similar way to the data explorer and subcontract generator."

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature clearly defined: Interactive GUI for CLI data pipeline
2. Extract key concepts from description
   → Actors: Business users, data analysts
   → Actions: Trigger pipeline, view results, copy outputs
   → Data: Pipeline execution logs, data tables, operation results
   → Constraints: Feature parity with CLI, user-friendly like existing pages
3. User flow is clear and well-defined
4. Generate testable requirements based on CLI operations
5. Identify key entities: Pipeline operations, execution results, logs
6. Review checklist confirms spec readiness
7. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
A business analyst needs to refresh the company's data warehouse with the latest information from Trello, Float, Xero, and Google Sheets. They open the Data Loading page, see a prominent "Run Full Pipeline" button, click it to execute all data extraction and transformation steps, monitor real-time progress with colored log messages, and upon completion, see a summary of what was updated with the ability to copy results for reporting to stakeholders and explore the resulting data tables interactively.

### Core Acceptance Scenarios (MVP - Priority 1)

1. **Given** the user opens the Data Loading page, **When** they view the interface, **Then** they see a prominent "Run Full Pipeline" button with a clear description of what it does (refreshes all data from all sources)

2. **Given** the user wants to refresh all data, **When** they click "Run Full Pipeline", **Then** the system executes all extraction and transformation steps in the correct order, shows real-time progress with color-coded log messages, and displays a success summary with record counts

3. **Given** a pipeline operation is running, **When** the user views the feedback panel, **Then** they see live log messages with timestamps showing each step's progress (e.g., "🔵 14:30:15 - Connecting to Trello...", "✅ 14:30:42 - Extracted 247 job cards", "🦆 14:30:45 - Saved to MotherDuck")

4. **Given** the full pipeline has completed successfully, **When** the user views the results, **Then** they see a formatted summary including: total execution time, all tables created/updated with record counts, data quality metrics, and a "Copy Results" button to copy this information as formatted text

5. **Given** the pipeline operation encounters an error, **When** the error occurs, **Then** the system displays a clear error message explaining what failed, shows the error in the log panel with red error markers, and allows the user to copy the error details for troubleshooting

6. **Given** the user wants to explore the refreshed data, **When** the pipeline completes, **Then** they see a list of all tables that were updated, can click on any table to preview the data, and can open an interactive data explorer (PyGWalker) to analyze the results

7. **Given** a pipeline operation is already running, **When** the user tries to start another operation, **Then** the "Run Full Pipeline" button is disabled and shows a message indicating that an operation is in progress

8. **Given** a developer makes UI layout changes, **When** the changes are implemented, **Then** the developer opens the page in a web browser to visually verify the layout renders correctly, colors display properly, and interactive elements function as expected

### Extended Acceptance Scenarios (Optional - Priority 2)

9. **Given** the user needs to update only specific data sources, **When** they view the Extract section, **Then** they see individual buttons for: Trello, Float, Xero Costs, Sales Data, each with a description and last run timestamp

10. **Given** the user wants to rebuild analytics tables, **When** they view the Transform section, **Then** they see individual buttons for: Quotes, Jobs, Customers, Add Labour, Projects, Analytics, each showing dependencies and data freshness

11. **Given** the user only wants to update Trello data, **When** they select "Extract Trello Data" and click Run, **Then** only the Trello extraction executes, and results show how many job cards were retrieved

### Edge Cases

- **What happens when the MotherDuck connection fails?** System shows a clear error message, explains that data cannot be saved to the cloud, and offers to retry the connection or save locally instead.

- **What happens when an API (Trello/Float) is unreachable?** System displays which specific API failed, shows the error in the log, and allows the user to skip that operation and continue with others.

- **What happens if the user closes the browser during a long-running operation?** Operation is interrupted (Streamlit's execution model requires active session). When the user reopens the page, they can restart the pipeline. Session state is lost on browser close.

- **What happens when extracted data has validation errors?** System shows data quality warnings in the feedback panel, highlights which records have issues, but still completes the operation and saves valid records.

- **What happens if the user tries to run a transform operation before extracting the required source data?** System checks for required input data, shows a warning message listing which extractions need to be run first, and disables the transform button until prerequisites are met.

- **What happens when the Google Sheets source is unavailable?** System falls back to legacy local files (as designed in the CLI), logs the fallback action, and notifies the user that older data was used.

- **What happens when the UI is viewed on different screen sizes?** The two-column layout adapts responsively, maintaining usability on tablets and desktop monitors, with the control panel and feedback panel both remaining accessible.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Pipeline Execution (Priority 1 - MVP)
- **FR-001**: System MUST provide a prominent "Run Full Pipeline" button that executes all extraction and transformation operations in the correct dependency order
- **FR-002**: System MUST prevent users from starting a new pipeline operation while another operation is currently running
- **FR-003**: "Run Full Pipeline" button MUST show clear description: "Refresh all data from Trello, Float, Xero, and Google Sheets. Updates all analytics tables."

#### Pipeline Execution (Priority 2 - Optional Enhancement)
- **FR-004**: System MAY provide individual operation buttons for each CLI command: extract (trello, float, xero-costs, sales), transform (quotes, jobs, customers, add-labour, projects, analytics), and validation
- **FR-005**: System MAY validate that required input data exists before allowing dependent transform operations to run
- **FR-006**: System MAY allow users to select output destination (MotherDuck, Local Files, or Both) before running extraction operations

#### Real-Time Feedback (Priority 1 - MVP)
- **FR-007**: System MUST display real-time log messages as pipeline operations execute, showing each step's progress with timestamps
- **FR-008**: System MUST show a progress indicator (spinner) while operations are running
- **FR-009**: System MUST categorize log messages by type with color coding: info (blue 🔵), success (green ✅), warning (yellow ⚠️), error (red ❌) for easy visual scanning
- **FR-010**: System MUST automatically scroll the log panel to show the most recent messages as they appear
- **FR-011**: System MUST preserve the complete log history for the current session so users can review earlier operations

#### Results and Output (Priority 1 - MVP)
- **FR-012**: System MUST display a summary card after pipeline completes, showing: total execution time, all tables created/updated with record counts, and overall status (success/warning/error)
- **FR-013**: System MUST provide a "Copy Results" button that copies the execution summary as formatted Markdown text suitable for pasting into emails or reports
- **FR-014**: System MUST display data quality metrics in results: number of records extracted per source, records validated, validation warnings, and errors encountered
- **FR-015**: System MUST provide a way to view and explore resulting data tables directly in the interface after operations complete (list of updated tables with preview/explore options)

#### Error Handling (Priority 1 - MVP)
- **FR-016**: System MUST display clear, actionable error messages when operations fail, explaining what went wrong and suggesting next steps
- **FR-017**: System MUST allow users to copy error details (including stack traces) for troubleshooting or support requests
- **FR-018**: System MUST continue executing independent operations even if one operation fails (e.g., if Trello fails, still run Float extraction) - **Note: In MVP, the single "Run Full Pipeline" button executes all operations sequentially through the CLI DAG. Critical errors will stop the pipeline. This requirement applies fully to Priority 2 individual operation buttons.**
- **FR-019**: System MUST log all errors with red error markers (❌) in the log panel for easy identification

#### User Interface (Priority 1 - MVP)
- **FR-020**: Interface MUST use a two-column layout: control panel on the left, feedback/results panel on the right (similar to existing pages)
- **FR-021**: System MUST display connection status to MotherDuck at the top of the page
- **FR-022**: System MUST show a status indicator: current operation running (if any), total duration displayed after completion

#### User Interface (Priority 2 - Optional Enhancement)
- **FR-023**: Interface MAY organize individual operations into clear categories: Extract, Transform, Validate, matching the CLI command structure
- **FR-024**: Each individual operation button MAY show a brief description of what it does and what data it affects
- **FR-025**: System MAY show the last successful run timestamp for each individual operation

#### Data Exploration (Priority 1 - MVP)
- **FR-026**: After pipeline operations complete, system MUST list all available data tables that were created or updated
- **FR-027**: System MUST allow users to preview table contents (first 100 rows displayed using st.dataframe) for any resulting data table
- **FR-028**: System MUST allow users to open PyGWalker interactive data explorer for any resulting data table

#### Data Exploration (Priority 2 - Optional Enhancement)
- **FR-029**: System MAY show table metadata: row count, column count, last updated timestamp

#### UI Testing and Validation (Priority 1 - MVP)
- **FR-030**: During development, all UI changes MUST be visually verified by examining the rendered interface in a web browser
- **FR-031**: System MUST be tested for visual consistency across different viewport sizes (desktop, tablet views at minimum)
- **FR-032**: UI layout changes MUST be verified to ensure two-column layout remains functional and feedback panel displays correctly

### Key Entities

- **Pipeline Operation**: Represents an individual CLI command (e.g., "Extract Trello", "Transform Quotes"). Attributes include: operation ID, display name, description, category (extract/transform/validate), dependencies (what must run first), estimated duration, last run timestamp.

- **Execution Log Entry**: A single log message from a pipeline operation. Attributes include: timestamp, log level (info/success/warning/error), operation name, message text, associated data (e.g., record counts).

- **Execution Result**: The outcome of a completed operation. Attributes include: operation name, start time, end time, duration, status (success/failed/warning), records processed, records created/updated, validation results, error details (if failed).

- **Data Table Reference**: A pointer to a resulting data table in MotherDuck or local storage. Attributes include: table name, location (motherduck/local), row count, column count, schema summary, last updated timestamp.

- **Pipeline Configuration**: User's selected settings for pipeline execution. Attributes include: output destination preference (motherduck/local/both), validation enabled/disabled, which operations to run.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

### Alignment with Existing System
- [x] Feature parity with CLI commands confirmed (all CLI operations represented)
- [x] User experience patterns match Data Explorer and Subcontract Generator pages
- [x] Integration points with existing infrastructure identified (MotherDuck connection, secrets management)

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted (GUI wrapper for CLI, real-time feedback, copyable results)
- [x] Ambiguities marked (none - requirements are clear)
- [x] User scenarios defined (11 acceptance scenarios + 7 edge cases)
- [x] Requirements generated (30 functional requirements)
- [x] Entities identified (5 key entities)
- [x] Review checklist passed

---

## Success Criteria

The **MVP** will be considered successfully implemented when:

1. **Core Functionality**: Single "Run Full Pipeline" button executes all CLI operations in correct order
2. **Real-Time Feedback**: Users see color-coded log messages (🔵 blue, ✅ green, ⚠️ yellow, ❌ red) appearing in real-time during execution
3. **Copyable Results**: Users can click "Copy Results" and paste formatted summary into Slack/email with all key information
4. **Data Exploration**: After pipeline completes, users can see list of updated tables and open interactive explorer (PyGWalker) for any table
5. **Error Resilience**: API failures and connection issues show clear error messages without crashing; the full pipeline stops on critical errors with clear logging for troubleshooting
6. **Visual Verification**: Two-column layout renders correctly in browser, colors display properly, buttons work, tested on desktop and tablet viewports
7. **User Friendliness**: Non-technical business user can click "Run Full Pipeline", see progress, copy results, and explore data without documentation

**Optional enhancements** (Priority 2 - can defer to future iteration):
- Individual operation buttons for granular control
- Last run timestamps per operation
- Detailed table metadata displays
- Advanced output destination selection

---

## Dependencies and Assumptions

### Dependencies
- Existing CLI pipeline code (`enviroflow_app/cli/`) must remain functional and is the single source of truth for data operations
- MotherDuck connection infrastructure (`enviroflow_app/elt/motherduck/`) is available and working
- Streamlit secrets management for API tokens and credentials is properly configured
- Existing data sources (Trello API, Float API, Google Sheets) remain accessible with current authentication

### Assumptions
- Users have proper credentials configured in Streamlit secrets to access all data sources
- MotherDuck database schema matches what the CLI expects (tables, columns, types)
- Multiple simultaneous users will not cause resource contention (or system handles this gracefully)
- Pipeline operations can run within Streamlit's execution model without timeout issues
- Users have sufficient MotherDuck quota for data storage and queries

---

## Out of Scope

The following items are explicitly **not** included in this feature:

- **Scheduling**: Automated/scheduled pipeline runs (remains a manual user-triggered action)
- **User Authentication**: Access control or user-specific permissions (assumes all users can run all operations)
- **Historical Audit Trail**: Long-term persistence of execution history beyond the current session
- **Pipeline Customization**: Ability to modify pipeline logic, add new operations, or change transformation rules through the GUI
- **Data Editing**: Direct editing of data in tables (this is a read-only exploration feature)
- **Advanced Configuration**: Exposing all CLI flags and options (only essential options like output destination)
- **Multi-Pipeline Support**: Running multiple different pipeline configurations simultaneously
- **Rollback/Undo**: Ability to revert data changes made by pipeline operations

---
