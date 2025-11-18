# Feature Specification: Simplify Data Loading ELT GUI

**Feature Branch**: `004-simplify-data-loading`
**Created**: 2025-10-02
**Status**: Draft
**Input**: User description: "Simplify Data Loading ELT GUI: Remove extraction/transform tabs, show only recently updated tables, consolidate notification display, remove duplicate info"

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature requirements identified: simplification, consolidation, selective display
2. Extract key concepts from description
   → Remove: extraction-only and transform-only tabs
   → Remove: individual operations tab
   → Consolidate: notification displays (remove duplication)
   → Filter: show only recently updated tables in exploration
3. Identify implementation scope
   → GUI simplification (removal of UI elements)
   → Data filtering logic (recent tables only)
   → Notification system consolidation
4. Fill User Scenarios & Testing section
   → Primary flow: Run full pipeline only
   → Secondary flow: View recently updated tables
5. Generate Functional Requirements
   → All requirements testable via UI inspection
6. Run Review Checklist
   → SUCCESS: All business requirements clear
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing

### Primary User Story
As a data analyst, I want a simplified pipeline interface where I can:
1. Run the complete data refresh with a single action
2. Monitor pipeline execution through clear, non-redundant notifications
3. Explore only the tables that were recently updated (relevant to current run)
4. See all execution feedback in one consolidated area

**Current Pain Points**:
- Too many tabs for operations I don't use (extraction-only, transform-only, individual operations)
- Duplicate notification information displayed in multiple places
- Table explorer shows ALL tables from database, not just recently updated ones
- Cluttered interface makes it hard to focus on the main task

### Acceptance Scenarios

#### Scenario 1: Run Pipeline
1. **Given** user is on the Data Loading ELT page
2. **When** user views the Control Panel
3. **Then** only one action is visible: "Run Full Pipeline" button
4. **And** no tabs for extraction-only, transform-only, or individual operations are shown

#### Scenario 2: Monitor Execution
1. **Given** pipeline is running
2. **When** user views notifications
3. **Then** notifications appear as toast messages (temporary popups)
4. **And** a single "Recent Notifications" section in sidebar shows persistent history
5. **And** no duplicate notification information appears elsewhere

#### Scenario 3: Explore Results
1. **Given** pipeline has completed successfully
2. **When** user navigates to "Explore Results" section
3. **Then** table dropdown shows only tables updated in the most recent run
4. **And** system displays timestamp/indicator for when each table was last updated
5. **And** all historical tables are excluded from the dropdown

#### Scenario 4: View Notification History
1. **Given** pipeline execution has completed
2. **When** user views the sidebar
3. **Then** "Recent Notifications" section shows all notifications from the run
4. **And** each notification shows: timestamp, status icon, and message
5. **And** notifications persist even after toast messages disappear

### Edge Cases
- What happens when no pipeline has been run yet? → Show message "No tables available. Run pipeline first."
- What happens if pipeline runs but no tables are updated? → Show message "No tables were updated in this run."
- How long do notifications persist? → Cleared when new pipeline run starts; last 20 shown.
- What if user wants to see older tables? → [NEEDS CLARIFICATION: Should there be a toggle/checkbox to "Show all tables"?]

## Requirements

### Functional Requirements

#### GUI Simplification
- **FR-001**: System MUST remove the "Extraction Only" tab from Control Panel
- **FR-002**: System MUST remove the "Transformation Only" tab from Control Panel
- **FR-003**: System MUST remove the "Individual Operations" tab from Control Panel
- **FR-004**: System MUST display only "Run Full Pipeline" button in the Control Panel
- **FR-005**: System MUST remove duplicate notification displays (if "Execution Log" and "Recent Notifications" show same info, keep only "Recent Notifications")

#### Notification Consolidation
- **FR-006**: System MUST display notifications as toast messages during pipeline execution (real-time ephemeral feedback)
- **FR-007**: System MUST persist all notifications in sidebar "Recent Notifications" section after toast disappears
- **FR-008**: System MUST clear notification history when new pipeline run starts
- **FR-009**: System MUST display maximum 20 recent notifications (newest first)
- **FR-010**: Each notification MUST show: timestamp, status icon (🔄/✅/❌), and descriptive message
- **FR-011**: System MUST NOT duplicate notification information in multiple sections

#### Recent Tables Filter
- **FR-012**: System MUST track which tables were created or updated during each pipeline run
- **FR-013**: "Explore Results" dropdown MUST show only tables from most recent pipeline execution
- **FR-014**: System MUST display indicator showing when each table was last updated
- **FR-015**: System MUST exclude all historical/unchanged tables from dropdown by default
- **FR-016**: If no tables were updated in recent run, system MUST display message: "No tables updated in this run"
- **FR-017**: If no pipeline has run yet, system MUST display message: "No tables available. Run pipeline first."

#### Retained Functionality
- **FR-018**: System MUST preserve connection status display in sidebar
- **FR-019**: System MUST preserve current operation status display (running indicator with elapsed time)
- **FR-020**: System MUST preserve execution summary display after run completes
- **FR-021**: System MUST preserve table preview functionality (first 100 rows)
- **FR-022**: System MUST preserve interactive PyGWalker explorer functionality
- **FR-023**: System MUST preserve copy results button with markdown export

### Key Entities

- **Pipeline Execution**: Represents a single run of the full ELT pipeline
  - Tracks: start time, end time, status (running/success/error)
  - Produces: list of updated tables, notifications, execution summary

- **Table Update Record**: Metadata about when a table was last modified
  - Tracks: table name, last update timestamp, update source (which pipeline run)
  - Used for: filtering "recently updated" tables in explorer

- **Notification Entry**: A single notification message displayed to user
  - Attributes: timestamp, status (start/complete/error), icon, message text
  - Lifecycle: appears as toast → persists in sidebar history → cleared on next run

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] One [NEEDS CLARIFICATION] marker identified (show all tables toggle - optional enhancement)
- [x] Requirements are testable and unambiguous via UI inspection
- [x] Success criteria are measurable (count tabs, check notification sections)
- [x] Scope is clearly bounded (GUI simplification only)
- [x] Dependencies: None - self-contained GUI changes

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted (remove tabs, consolidate notifications, filter tables)
- [x] Ambiguities marked (1 optional enhancement noted)
- [x] User scenarios defined (4 scenarios, edge cases identified)
- [x] Requirements generated (23 functional requirements)
- [x] Entities identified (3 entities: Pipeline Execution, Table Update Record, Notification Entry)
- [x] Review checklist passed

---

## Business Value

### Problem Being Solved
Users are overwhelmed by too many options and duplicate information in the current Data Loading ELT interface. The extraction-only, transform-only, and individual operations are rarely used but take up significant screen space. Duplicate notification displays create confusion about which feedback to trust. The table explorer showing ALL database tables (not just recent updates) makes it hard to focus on relevant results.

### Expected Benefits
- **Reduced Cognitive Load**: Single clear action ("Run Full Pipeline") eliminates decision paralysis
- **Cleaner Interface**: Removing 75% of tabs reduces visual clutter
- **Better Focus**: Showing only recently updated tables helps users verify their work
- **Clearer Feedback**: Single source of truth for notifications eliminates confusion
- **Faster Navigation**: Fewer UI elements means faster task completion

### Success Metrics
- User completes pipeline run with fewer clicks (baseline: 2 clicks to reach tab, target: 1 click for button)
- Reduction in support questions about "which operation should I run?"
- User spends less time searching through table list (showing 5-10 recent vs 40+ historical)
- Positive user feedback on simplified interface

---
