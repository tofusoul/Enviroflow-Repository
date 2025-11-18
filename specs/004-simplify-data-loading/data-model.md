# Data Model: GUI Simplification

**Feature**: Simplify Data Loading ELT GUI
**Branch**: `004-simplify-data-loading`
**Date**: 2025-10-02

## Overview

This feature has minimal data model changes. All changes are to **session state** (ephemeral, in-memory data) and **UI presentation logic**. No database schema changes required.

---

## Session State Entities

### 1. Recently Updated Tables List

**Purpose**: Track which tables were created or modified during the most recent pipeline execution.

**Storage**: `st.session_state.recently_updated_tables`

**Type**: `list[str]`

**Lifecycle**:
- **Initialized**: Empty list when page loads
- **Populated**: During `execute_pipeline_with_progress()` as each task completes
- **Cleared**: When new pipeline run starts (in `run_full_pipeline()`)
- **Used by**: Table dropdown filter in "Explore Results" section

**Example Value**:
```python
[
    "projects_for_analytics",
    "quotes",
    "jobs",
    "customers",
    "labour_hours"
]
```

**Business Rules**:
- Table names are unique (no duplicates)
- Order doesn't matter (dropdown will sort alphabetically)
- Empty list means "no recent updates" → show message to user
- List persists until new pipeline run or page refresh

---

### 2. Notification Entry (Enhanced)

**Purpose**: Store notification messages for persistent display in sidebar.

**Storage**: `st.session_state.toast_history`

**Type**: `list[NotificationEntry]` where `NotificationEntry` is:

```python
TypedDict("NotificationEntry", {
    "timestamp": str,        # Format: "HH:MM:SS"
    "icon": str,             # One of: "🔄", "✅", "❌"
    "status": str,           # One of: "start", "complete", "error"
    "message": str,          # Human-readable description
})
```

**Lifecycle**:
- **Initialized**: Empty list when page loads
- **Populated**: By `show_step_notification()` during pipeline execution
- **Displayed**: In sidebar "Recent Notifications" section
- **Cleared**: When new pipeline run starts
- **Trimmed**: Keep last 20 entries only

**Example Value**:
```python
[
    {
        "timestamp": "14:32:15",
        "icon": "🔄",
        "status": "start",
        "message": "Starting: Extract Trello data"
    },
    {
        "timestamp": "14:32:18",
        "icon": "✅",
        "status": "complete",
        "message": "Completed: Extract Trello data"
    },
    {
        "timestamp": "14:32:19",
        "icon": "🔄",
        "status": "start",
        "message": "Starting: Build quotes table"
    }
]
```

**Business Rules**:
- Notifications are append-only (never modified after creation)
- Maximum 20 entries (oldest auto-deleted when limit exceeded)
- Displayed newest-first in UI (reverse order)
- Status determines display style (info/success/error)

---

### 3. Removed Session State

**Deleted**: `st.session_state.notification_placeholder`

**Reason**: No longer needed. Original implementation attempted to update placeholder during execution (doesn't work in Streamlit). New implementation uses natural rendering after execution completes.

---

## UI State Changes

### Control Panel Structure

**Before** (4 tabs):
```
tab_full, tab_extract, tab_transform, tab_individual = st.tabs([...])
```

**After** (No tabs):
```
# Single section with one button
st.button("🚀 Run Full Pipeline")
```

**Impact**: Simpler state management, no tab selection tracking needed.

---

### Table Dropdown Options

**Before**:
```python
options = st.session_state.available_tables  # All tables from database
```

**After**:
```python
# Filter to recent tables only
if st.session_state.recently_updated_tables:
    options = st.session_state.recently_updated_tables
else:
    options = []  # Show empty state message
```

**Impact**: Users see fewer options, focused on relevant results.

---

## Validation Rules

### Recently Updated Tables
- **Rule 1**: List must contain valid table names (strings)
- **Rule 2**: Table names must exist in MotherDuck (validation can be added later if needed)
- **Rule 3**: List is cleared at pipeline start (prevents stale data)

### Notification Entries
- **Rule 1**: Timestamp must be valid "HH:MM:SS" format
- **Rule 2**: Status must be one of: "start", "complete", "error"
- **Rule 3**: Icon must match status:
  - "start" → "🔄"
  - "complete" → "✅"
  - "error" → "❌"
- **Rule 4**: Message must be non-empty string

---

## Data Flow Diagram

```
Pipeline Execution
       ↓
execute_pipeline_with_progress()
       ↓
    [For each task]
       ↓
   ┌───────────────────┐
   │ Task Executes     │
   └───────────────────┘
           ↓
   ┌───────────────────────────────────┐
   │ show_step_notification()          │
   │   • Create notification entry     │
   │   • Append to toast_history       │
   │   • Show toast popup             │
   └───────────────────────────────────┘
           ↓
   ┌───────────────────────────────────┐
   │ Capture updated tables            │
   │   • Query MotherDuck metadata     │
   │   • Add to recently_updated_tables│
   └───────────────────────────────────┘
           ↓
    Sidebar Renders
       ↓
   ┌───────────────────────────────────┐
   │ "Recent Notifications" Display    │
   │   • Read toast_history            │
   │   • Show newest 20 (reversed)     │
   │   • Color code by status          │
   └───────────────────────────────────┘
           ↓
   "Explore Results" Renders
       ↓
   ┌───────────────────────────────────┐
   │ Table Dropdown                    │
   │   • Read recently_updated_tables  │
   │   • Filter dropdown options       │
   │   • Show empty state if needed    │
   └───────────────────────────────────┘
```

---

## No Database Schema Changes

This feature requires **ZERO** database schema modifications:
- ✅ No new tables
- ✅ No column additions
- ✅ No index changes
- ✅ No migration scripts

All data is ephemeral (session state only).

---

## Relationships

### Notification Entry → Pipeline Execution
- **Cardinality**: Many notifications per pipeline run
- **Relationship**: Notifications are generated during pipeline execution
- **Cascading**: Notifications cleared when new pipeline starts

### Recently Updated Tables → Pipeline Execution
- **Cardinality**: Multiple tables per pipeline run
- **Relationship**: Tables tracked during pipeline execution
- **Cascading**: List cleared when new pipeline starts

### Table Dropdown → Recently Updated Tables
- **Cardinality**: One-to-many (dropdown shows subset of available tables)
- **Relationship**: Dropdown options filtered by recently_updated_tables list
- **Constraint**: If recently_updated_tables is empty, dropdown is empty

---

## Testing Requirements

### Unit Tests (Session State Management)
```python
def test_recently_updated_tables_initialization():
    """Test that recently_updated_tables starts empty."""

def test_recently_updated_tables_population():
    """Test adding tables during pipeline execution."""

def test_recently_updated_tables_cleared_on_new_run():
    """Test that list is cleared when new pipeline starts."""

def test_notification_entry_creation():
    """Test creating valid notification entries."""

def test_notification_entry_validation():
    """Test invalid notification entries are rejected."""

def test_toast_history_max_size():
    """Test that toast_history never exceeds 20 entries."""
```

### Integration Tests (UI Behavior)
```python
def test_table_dropdown_shows_recent_tables_only():
    """Test table dropdown filters to recent tables."""

def test_table_dropdown_empty_state():
    """Test empty state when no recent tables."""

def test_notifications_display_in_sidebar():
    """Test notifications appear in sidebar section."""

def test_notifications_cleared_on_new_run():
    """Test notifications clear when new pipeline starts."""
```

---

## Summary

This feature's data model is **extremely simple**:
- Two session state lists (strings and dictionaries)
- No database changes
- No complex relationships
- Ephemeral data only

The simplicity reflects the Simplicity-First constitutional principle. All changes are UI presentation layer only.
