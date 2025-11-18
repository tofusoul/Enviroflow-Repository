"""Integration tests for simplified Data Loading ELT GUI.

Tests UI behavioral contracts for the simplified interface by checking
the actual file content rather than importing (since module has emoji in name).

Contract Coverage:
- Contract 1: Control Panel has single button, no tabs
- Contract 2: Consolidated notifications (no duplicate Execution Log)
- Contract 3: Filtered table dropdown (recent tables only)
- Contract 4: Session state management
- Contract 5: Toast notifications
- Contract 6: Preserved functionality
"""

import pytest
from pathlib import Path


# Path to the GUI file under test
GUI_FILE_PATH = Path("enviroflow_app/pages/6_🚚_Data_Loading_ELT.py")


class TestControlPanelStructure:
    """Test Contract 1: Control Panel has single button, no tabs."""

    def test_control_panel_single_button_no_tabs(self):
        """Verify control panel shows only one button, no tabs.

        Expected to FAIL until tabs are removed (T014).
        Checks file content for st.tabs() calls.
        """
        # Read the GUI file
        content = GUI_FILE_PATH.read_text()

        # Expected: NO st.tabs() calls in control panel section
        # Count occurrences of st.tabs
        tabs_count = content.count("st.tabs(")
        assert (
            tabs_count == 0
        ), f"Expected 0 st.tabs() calls, found {tabs_count}. Tabs should be removed."

        # Expected: "Run Full Pipeline" button exists
        assert (
            "Run Full Pipeline" in content
        ), "Expected 'Run Full Pipeline' button to exist"


class TestNotificationConsolidation:
    """Test Contract 2: Sidebar has only Recent Notifications (no Execution Log)."""

    def test_sidebar_single_notification_section(self):
        """Verify sidebar has only Recent Notifications, no Execution Log.

        Expected to FAIL until Execution Log is removed (T015).
        """
        content = GUI_FILE_PATH.read_text()

        # Expected: "Recent Notifications" section exists
        assert (
            "Recent Notifications" in content
        ), "Expected 'Recent Notifications' section to exist"

        # Expected: "Execution Log" section does NOT exist
        assert (
            "Execution Log" not in content
        ), "Expected NO 'Execution Log' section. Should be removed (duplicate)."


class TestTableDropdownFiltering:
    """Test Contract 3: Table dropdown shows only recent tables."""

    def test_table_dropdown_has_filtering_logic(self):
        """Verify table dropdown has filtering logic for recent tables.

        Expected to FAIL until table filtering is implemented (T019).
        """
        content = GUI_FILE_PATH.read_text()

        # Expected: recently_updated_tables variable is referenced
        assert (
            "recently_updated_tables" in content
        ), "Expected 'recently_updated_tables' to be used for filtering"

        # Expected: Filter logic in place (checking for filtered list)
        # Look for filtering pattern in Explore Results section
        assert (
            "recent_tables" in content or "filtered_tables" in content
        ), "Expected filtering logic for recent tables"


class TestSessionStateInitialization:
    """Test Contract 4: Pipeline execution flow with session state."""

    def test_recently_updated_tables_initialization(self):
        """Verify recently_updated_tables session state variable is initialized.

        Expected to FAIL until session state is initialized (T016).
        """
        content = GUI_FILE_PATH.read_text()

        # Expected: recently_updated_tables initialization exists
        # Look for initialization pattern
        has_init = (
            'recently_updated_tables" not in st.session_state' in content
            or "recently_updated_tables = []" in content
        )
        assert (
            has_init
        ), "Expected 'recently_updated_tables' initialization in session state"


class TestRemovedFunctionsGone:
    """Test that unused functions have been removed."""

    def test_extraction_pipeline_function_removed(self):
        """Verify run_extraction_pipeline() function is removed.

        Expected to FAIL until function is deleted (T011).
        """
        content = GUI_FILE_PATH.read_text()

        assert (
            "def run_extraction_pipeline" not in content
        ), "Expected run_extraction_pipeline() to be removed (unused)"

    def test_transform_pipeline_function_removed(self):
        """Verify run_transform_pipeline() function is removed.

        Expected to FAIL until function is deleted (T012).
        """
        content = GUI_FILE_PATH.read_text()

        assert (
            "def run_transform_pipeline" not in content
        ), "Expected run_transform_pipeline() to be removed (unused)"


class TestTabsRemoved:
    """Test that all 4 tabs are removed."""

    def test_no_extraction_only_tab(self):
        """Verify 'Extraction Only' tab is removed.

        Expected to FAIL until tab is deleted (T011).
        """
        content = GUI_FILE_PATH.read_text()

        assert (
            "Extraction Only" not in content
        ), "Expected 'Extraction Only' tab to be removed"

    def test_no_transformation_only_tab(self):
        """Verify 'Transformation Only' tab is removed.

        Expected to FAIL until tab is deleted (T012).
        """
        content = GUI_FILE_PATH.read_text()

        assert (
            "Transformation Only" not in content
        ), "Expected 'Transformation Only' tab to be removed"

    def test_no_individual_operations_tab(self):
        """Verify 'Individual Operations' tab is removed.

        Expected to FAIL until tab is deleted (T013).
        """
        content = GUI_FILE_PATH.read_text()

        assert (
            "Individual Operations" not in content
        ), "Expected 'Individual Operations' tab to be removed"


class TestPreservedFunctionality:
    """Test Contract 6: Retained features still work."""

    def test_explore_results_section_preserved(self):
        """Verify 'Explore Results' section still exists.

        Should PASS - validates no regression.
        """
        content = GUI_FILE_PATH.read_text()

        # Expected: "Explore Results" section exists
        assert (
            "Explore Results" in content
        ), "Expected 'Explore Results' section to be preserved"

    def test_table_selector_preserved(self):
        """Verify table selector (selectbox) still exists.

        Should PASS - validates no regression.
        """
        content = GUI_FILE_PATH.read_text()

        # Expected: selectbox for table selection
        assert (
            "Select a table to explore" in content or "selectbox" in content
        ), "Expected table selector to be preserved"

    def test_pygwalker_integration_preserved(self):
        """Verify PyGWalker interactive explorer still exists.

        Should PASS - validates no regression.
        """
        content = GUI_FILE_PATH.read_text()

        # Expected: PyGWalker integration code
        assert (
            "pygwalker" in content or "StreamlitRenderer" in content
        ), "Expected PyGWalker integration to be preserved"


# Mark all tests as integration tests
pytestmark = pytest.mark.integration
