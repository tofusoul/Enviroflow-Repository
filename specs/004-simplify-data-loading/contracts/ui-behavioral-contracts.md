# UI Behavioral Contracts

**Feature**: Simplify Data Loading ELT GUI
**Branch**: `004-simplify-data-loading`
**Date**: 2025-10-02

## Overview

Since this is a Streamlit GUI feature (not a REST API), we define **UI behavioral contracts** instead of API endpoint contracts. These specify the expected behavior of UI components.

---

## Contract 1: Control Panel Structure

**Component**: Control Panel section
**Location**: Main page content area
**User Story**: FR-001 through FR-004 (GUI Simplification)

### Expected UI State

```yaml
component: "Control Panel"
structure:
  heading:
    text: "⚙️ Control Panel"
    type: "st.header"

  content:
    - type: "st.markdown"
      text: "**Run Full Pipeline**\nExecutes the complete ELT pipeline..."

    - type: "st.button"
      label: "🚀 Run Full Pipeline"
      style: "primary"
      full_width: true
      disabled: false  # when can_start_pipeline() is True

  removed_elements:
    - "st.tabs with 4 tab options"
    - "Extraction Only tab"
    - "Transformation Only tab"
    - "Individual Operations tab"
```

### Test Contract

```python
def test_control_panel_has_single_button():
    """Verify control panel shows only one button, no tabs."""
    # Expected: One button, no tabs
    assert count_elements("st.tabs") == 0
    assert count_elements("st.button", label_contains="Run Full Pipeline") == 1
    assert count_elements("st.button") == 1  # Only one button total
```

---

## Contract 2: Notification Display

**Component**: Recent Notifications section
**Location**: Sidebar
**User Story**: FR-006 through FR-011 (Notification Consolidation)

### Expected UI State

```yaml
component: "Recent Notifications"
location: "sidebar"
structure:
  expander:
    label: "📬 Recent Notifications"
    expanded: true
    max_items: 20

  content:
    - type: "notification_list"
      order: "newest_first"
      format:
        - timestamp: "HH:MM:SS"
        - icon: "🔄 | ✅ | ❌"
        - message: "string"

      display_method:
        start: "st.info(message, icon='🔄')"
        complete: "st.success(message, icon='✅')"
        error: "st.error(message, icon='❌')"

removed_components:
  - "📝 Execution Log section"
  - "Duplicate log container"
```

### Test Contract

```python
def test_sidebar_has_single_notification_section():
    """Verify sidebar has only Recent Notifications, no Execution Log."""
    # Expected: One notification section
    assert count_sidebar_sections("Recent Notifications") == 1
    assert count_sidebar_sections("Execution Log") == 0

def test_notification_entries_color_coded():
    """Verify notifications use correct color coding."""
    notifications = get_sidebar_notifications()
    for notif in notifications:
        if notif["status"] == "start":
            assert notif["display_type"] == "info"
        elif notif["status"] == "complete":
            assert notif["display_type"] == "success"
        elif notif["status"] == "error":
            assert notif["display_type"] == "error"
```

---

## Contract 3: Table Dropdown Filter

**Component**: Table selector dropdown
**Location**: Explore Results section
**User Story**: FR-012 through FR-017 (Recent Tables Filter)

### Expected UI State

```yaml
component: "Table Selector"
location: "Explore Results section"
behavior:
  data_source: "st.session_state.recently_updated_tables"
  filtering: "show_recent_only"
  empty_state:
    condition: "len(recently_updated_tables) == 0"
    message: "📭 No tables available yet. Run the pipeline to populate data."

  populated_state:
    condition: "len(recently_updated_tables) > 0"
    message: "✅ {count} tables available for exploration"
    dropdown:
      type: "st.selectbox"
      label: "Select a table to explore:"
      options: "recently_updated_tables"
      sort: "alphabetical"
```

### Test Contract

```python
def test_table_dropdown_filters_to_recent_tables():
    """Verify dropdown shows only recently updated tables."""
    # Setup
    run_pipeline()  # Populates recently_updated_tables

    # Expected: Dropdown shows only recent tables
    dropdown_options = get_table_dropdown_options()
    recent_tables = get_session_state("recently_updated_tables")

    assert set(dropdown_options) == set(recent_tables)
    assert len(dropdown_options) < 15  # Should be 5-10, not 40+

def test_table_dropdown_empty_state():
    """Verify empty state when no recent tables."""
    # Setup
    clear_session_state("recently_updated_tables")

    # Expected: Empty state message
    assert element_contains_text("📭 No tables available yet")
    assert count_elements("st.selectbox") == 0  # Dropdown hidden/disabled
```

---

## Contract 4: Pipeline Execution Flow

**Component**: Pipeline execution with table tracking
**Location**: Backend logic (execute_pipeline_with_progress)
**User Story**: FR-012 (Track updated tables)

### Expected Behavior

```yaml
pipeline_execution:
  initialization:
    - clear "recently_updated_tables"
    - clear "toast_history"

  during_execution:
    - for each task:
        - show_step_notification("start")
        - execute task
        - capture updated tables
        - append to "recently_updated_tables"
        - show_step_notification("complete" or "error")

  completion:
    - session_state contains full list of updated tables
    - notifications preserved in toast_history
    - UI updates to show new tables
```

### Test Contract

```python
def test_recently_updated_tables_populated_during_execution():
    """Verify tables are tracked during pipeline execution."""
    # Setup
    clear_session_state("recently_updated_tables")

    # Execute
    run_full_pipeline()

    # Expected: Tables list populated
    recent_tables = get_session_state("recently_updated_tables")
    assert len(recent_tables) > 0
    assert "projects_for_analytics" in recent_tables
    assert "quotes" in recent_tables

def test_recently_updated_tables_cleared_on_new_run():
    """Verify tables list cleared when starting new pipeline."""
    # Setup
    set_session_state("recently_updated_tables", ["old_table"])

    # Execute
    start_pipeline()  # Just start, don't wait for completion

    # Expected: List cleared
    recent_tables = get_session_state("recently_updated_tables")
    assert len(recent_tables) == 0
```

---

## Contract 5: Toast Notification Behavior

**Component**: Toast notifications (ephemeral popups)
**Location**: Bottom-right corner of screen
**User Story**: FR-006 (Real-time feedback)

### Expected Behavior

```yaml
toast_notifications:
  triggering:
    - condition: "show_step_notification() called"
    - display: "st.toast(message, icon=icon)"

  appearance:
    start:
      icon: "🔄"
      message: "Starting: {task_description}"
    complete:
      icon: "✅"
      message: "Completed: {task_description}"
    error:
      icon: "❌"
      message: "Error: {error_message}"

  lifecycle:
    - appears: "immediately when called"
    - duration: "3-4 seconds"
    - disappears: "automatically"
    - persistence: "NOT persisted (ephemeral only)"
```

### Test Contract

```python
def test_toast_notifications_appear_during_execution():
    """Verify toast popups appear for each step."""
    # This test requires manual validation or Streamlit testing framework
    # Automated test would check function calls:

    with mock.patch("streamlit.toast") as mock_toast:
        show_step_notification("Test task", "start")
        mock_toast.assert_called_once_with(
            "🔄 Starting: Test task",
            icon="🔄"
        )

def test_toast_notifications_are_ephemeral():
    """Verify toasts don't persist in UI state."""
    # Toasts should NOT appear in any session state
    show_step_notification("Test", "complete")

    # Session state should only have persistent notifications
    assert "toast_messages" not in st.session_state  # No toast storage
    assert len(st.session_state.toast_history) > 0  # Persistent storage exists
```

---

## Contract 6: Preserved Functionality

**Component**: Retained features from original implementation
**Location**: Various
**User Story**: FR-018 through FR-023 (Retained Functionality)

### Expected Behavior (Unchanged)

```yaml
preserved_features:
  connection_status:
    location: "sidebar"
    function: "get_connection_status_message()"
    display: "st.success() or st.error()"

  current_operation_status:
    location: "sidebar"
    condition: "pipeline_running == True"
    display:
      - operation_name: "st.info()"
      - current_step: "st.caption()"
      - elapsed_time: "st.caption()"

  execution_summary:
    location: "sidebar"
    condition: "last_result exists"
    function: "display_execution_summary()"

  table_preview:
    location: "Explore Results"
    component: "st.expander()"
    content: "st.dataframe(first 100 rows)"

  pygwalker_explorer:
    location: "Explore Results"
    trigger: "st.button('Open Interactive Explorer')"
    content: "StreamlitRenderer(df).explorer()"

  copy_results:
    location: "Execution Summary"
    component: "st.expander('Copy Results')"
    content: "st.code(markdown_results)"
```

### Test Contract

```python
def test_connection_status_preserved():
    """Verify connection status display still works."""
    status = get_sidebar_element("connection_status")
    assert status is not None
    assert "MotherDuck" in status.text

def test_table_preview_preserved():
    """Verify table preview functionality still works."""
    select_table("projects_for_analytics")
    click_expander("Preview Table")

    dataframe = get_element("st.dataframe")
    assert dataframe is not None
    assert dataframe.row_count <= 100

def test_pygwalker_preserved():
    """Verify PyGWalker explorer still opens."""
    select_table("projects_for_analytics")
    click_button("Open Interactive Explorer")

    explorer = get_element("pygwalker_renderer")
    assert explorer is not None
```

---

## Test Execution Strategy

### Unit Tests (Python)
- Test session state management
- Test helper functions (`show_step_notification`)
- Mock Streamlit components

### Integration Tests (Manual + Automated)
- Use `quickstart.md` validation scenarios
- Consider Streamlit testing framework (if available)
- Manual UI validation for visual elements

### Regression Tests
- Run existing pipeline tests to ensure no breakage
- Verify data loading still works
- Check MotherDuck connectivity

---

## Success Criteria

**All contracts are satisfied when**:
1. ✅ Control panel shows single button, no tabs
2. ✅ Sidebar has one notification section (Recent Notifications)
3. ✅ Table dropdown shows only recent tables (5-10, not 40+)
4. ✅ Pipeline execution tracks updated tables
5. ✅ Toast notifications appear and disappear correctly
6. ✅ All preserved features function identically

**Validation Method**: Execute all test contracts + quickstart scenarios

---

## Notes

- These contracts are UI/behavioral, not REST API contracts
- Some tests require manual validation (visual elements)
- Streamlit's testing framework is limited compared to web frameworks
- Focus on functional testing over pixel-perfect UI testing
- Mock Streamlit components where possible for automated tests
