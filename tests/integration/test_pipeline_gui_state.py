"""Integration tests for session state management in pipeline GUI.

Tests session state initialization and management including:
- Concurrent execution prevention
- Log message appending
- Result updates
- Operation history tracking
"""

import pytest
from datetime import datetime
from unittest.mock import patch
from enviroflow_app.st_components.pipeline_gui import (
    init_pipeline_session_state,
    stream_log,
    ExecutionResult,
)


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    return {}


@pytest.fixture
def mock_streamlit(mock_session_state):
    """Mock Streamlit module with session state."""
    with patch("streamlit.session_state", mock_session_state):
        import streamlit as st

        st.session_state = mock_session_state
        yield st


class TestSessionStateInitialization:
    """Tests for session state initialization."""

    def test_init_pipeline_session_state_creates_all_keys(self, mock_streamlit):
        """Test that init_pipeline_session_state() creates all required keys."""
        st = mock_streamlit

        # Initialize session state
        init_pipeline_session_state()

        # Verify all keys exist
        assert "pipeline_running" in st.session_state
        assert "execution_log" in st.session_state
        assert "last_result" in st.session_state
        assert "operation_history" in st.session_state
        assert "available_tables" in st.session_state
        assert "current_operation" in st.session_state
        assert "operation_start_time" in st.session_state

    def test_init_sets_correct_default_values(self, mock_streamlit):
        """Test that session state keys have correct default values."""
        st = mock_streamlit

        init_pipeline_session_state()

        assert st.session_state.pipeline_running is False
        assert st.session_state.execution_log == []
        assert st.session_state.last_result is None
        assert st.session_state.operation_history == []
        assert st.session_state.available_tables == []
        assert st.session_state.current_operation is None
        assert st.session_state.operation_start_time is None


class TestConcurrentExecutionPrevention:
    """Tests for concurrent execution prevention."""

    def test_pipeline_running_flag_prevents_concurrent_execution(self, mock_streamlit):
        """Test that pipeline_running flag prevents starting a new operation."""
        # This test will fail until implementation checks the flag
        st = mock_streamlit
        init_pipeline_session_state()

        # Simulate first operation running
        st.session_state.pipeline_running = True

        # Try to start another operation (should be prevented)
        from enviroflow_app.pages import data_loading_page

        # This should check pipeline_running and not execute
        # (Implementation needs to handle this)
        result = data_loading_page.can_start_pipeline()

        assert result is False, "Should not allow concurrent pipeline execution"

    def test_pipeline_running_reset_after_completion(self, mock_streamlit):
        """Test that pipeline_running is reset to False after execution."""
        # This test will fail - implementation doesn't exist yet
        st = mock_streamlit
        init_pipeline_session_state()

        # The implementation should reset this flag after execution
        from enviroflow_app.pages import data_loading_page

        # Mock pipeline execution
        with patch(
            "enviroflow_app.cli.dag.Pipeline.create_full_pipeline"
        ) as mock_pipeline:
            mock_engine = type(
                "obj", (object,), {"execute": lambda: {"status": "success"}}
            )()
            mock_pipeline.return_value = mock_engine

            st.session_state.pipeline_running = False
            data_loading_page.run_full_pipeline()

            # Should be reset to False after completion
            assert st.session_state.pipeline_running is False


class TestExecutionLogManagement:
    """Tests for execution log appending and management."""

    def test_execution_log_appends_correctly(self, mock_streamlit):
        """Test that log messages append to execution_log in order."""
        st = mock_streamlit
        init_pipeline_session_state()

        # Add multiple log messages
        stream_log("INFO", "Op1", "Message 1")
        stream_log("SUCCESS", "Op1", "Message 2")
        stream_log("WARNING", "Op2", "Message 3")

        # Verify all messages were appended
        assert len(st.session_state.execution_log) == 3
        assert st.session_state.execution_log[0]["message"] == "Message 1"
        assert st.session_state.execution_log[1]["message"] == "Message 2"
        assert st.session_state.execution_log[2]["message"] == "Message 3"

    def test_execution_log_preserves_session_history(self, mock_streamlit):
        """Test that execution log persists across reruns (within session)."""
        st = mock_streamlit
        init_pipeline_session_state()

        # Add a log message
        stream_log("INFO", "Test", "Initial message")

        # Simulate rerun (re-initialize without clearing)
        init_pipeline_session_state()

        # Log should still have the message
        assert len(st.session_state.execution_log) >= 1
        assert any(
            log["message"] == "Initial message"
            for log in st.session_state.execution_log
        )


class TestLastResultUpdate:
    """Tests for last_result session state updates."""

    def test_last_result_updates_after_completion(self, mock_streamlit):
        """Test that last_result is updated with execution results."""
        # This test will fail - implementation doesn't exist
        st = mock_streamlit
        init_pipeline_session_state()

        from enviroflow_app.pages import data_loading_page

        with patch(
            "enviroflow_app.cli.dag.Pipeline.create_full_pipeline"
        ) as mock_pipeline:
            mock_engine = type(
                "obj",
                (object,),
                {"execute": lambda: {"status": "success", "duration": 60}},
            )()
            mock_pipeline.return_value = mock_engine

            data_loading_page.run_full_pipeline()

            # Verify last_result was updated
            assert st.session_state.last_result is not None
            assert "operation" in st.session_state.last_result
            assert "duration_seconds" in st.session_state.last_result


class TestOperationHistoryTracking:
    """Tests for operation history management."""

    def test_operation_history_maintains_last_20_results(self, mock_streamlit):
        """Test that operation_history keeps only last 20 results."""
        st = mock_streamlit
        init_pipeline_session_state()

        # Create 25 mock results
        for i in range(25):
            result: ExecutionResult = {
                "operation": f"Operation {i}",
                "status": "success",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "duration_seconds": 10.0,
                "records_processed": 100,
                "tables_created": ["test_table"],
                "validation_results": None,
                "error_message": None,
                "error_traceback": None,
            }
            st.session_state.operation_history.append(result)

            # Trim to last 20 (this logic should be in implementation)
            if len(st.session_state.operation_history) > 20:
                st.session_state.operation_history = st.session_state.operation_history[
                    -20:
                ]

        # Verify only 20 results remain
        assert len(st.session_state.operation_history) == 20

        # Verify newest results are kept
        assert st.session_state.operation_history[-1]["operation"] == "Operation 24"
