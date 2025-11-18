"""Integration tests for pipeline GUI execution functionality.

Tests the full pipeline execution workflow including:
- Pipeline function calls
- Session state updates
- Log message generation
- Error handling
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from enviroflow_app.st_components.pipeline_gui import stream_log


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    session_state = {
        "pipeline_running": False,
        "execution_log": [],
        "last_result": None,
        "operation_history": [],
        "available_tables": [],
        "current_operation": None,
        "operation_start_time": None,
    }
    return session_state


@pytest.fixture
def mock_streamlit(mock_session_state):
    """Mock Streamlit module with session state."""
    with patch("streamlit.session_state", mock_session_state):
        yield


class TestPipelineExecution:
    """Tests for full pipeline execution integration."""

    def test_run_full_pipeline_calls_pipeline_execute(self, mock_streamlit):
        """Test that run_full_pipeline() function calls Pipeline.create_full_pipeline().execute()."""
        # This test will fail until implementation is complete
        # We're testing the integration between GUI and CLI pipeline

        with patch(
            "enviroflow_app.cli.dag.Pipeline.create_full_pipeline"
        ) as mock_pipeline:
            mock_engine = MagicMock()
            mock_engine.execute.return_value = {
                "status": "success",
                "tasks_completed": 10,
                "duration": 125.5,
            }
            mock_pipeline.return_value = mock_engine

            # Import the function we're testing (will fail - not implemented yet)
            from enviroflow_app.pages import data_loading_page

            # This should call Pipeline.create_full_pipeline().execute()
            data_loading_page.run_full_pipeline()

            # Verify pipeline was created and executed
            mock_pipeline.assert_called_once()
            mock_engine.execute.assert_called_once()

    def test_execution_results_captured_in_session_state(
        self, mock_streamlit, mock_session_state
    ):
        """Test that execution results are stored in session state."""
        # This test will fail - implementation doesn't exist yet

        with patch(
            "enviroflow_app.cli.dag.Pipeline.create_full_pipeline"
        ) as mock_pipeline:
            mock_engine = MagicMock()
            mock_engine.execute.return_value = {
                "status": "success",
                "tasks_completed": 10,
            }
            mock_pipeline.return_value = mock_engine

            from enviroflow_app.pages import data_loading_page

            # Execute pipeline
            data_loading_page.run_full_pipeline()

            # Verify last_result was updated in session state
            assert mock_session_state["last_result"] is not None
            assert mock_session_state["last_result"]["status"] == "success"

    def test_log_messages_generated_during_execution(
        self, mock_streamlit, mock_session_state
    ):
        """Test that log messages are generated and appended to execution_log."""
        # This test will fail - logging not implemented yet

        with patch(
            "enviroflow_app.cli.dag.Pipeline.create_full_pipeline"
        ) as mock_pipeline:
            mock_engine = MagicMock()
            mock_engine.execute.return_value = {"status": "success"}
            mock_pipeline.return_value = mock_engine

            from enviroflow_app.pages import data_loading_page

            # Clear log before test
            mock_session_state["execution_log"] = []

            # Execute pipeline
            data_loading_page.run_full_pipeline()

            # Verify log messages were generated
            assert len(mock_session_state["execution_log"]) > 0

            # Check for start message
            start_logs = [
                log
                for log in mock_session_state["execution_log"]
                if "Starting" in log["message"] or "started" in log["message"].lower()
            ]
            assert len(start_logs) > 0

    def test_error_handling_when_pipeline_raises_exception(
        self, mock_streamlit, mock_session_state
    ):
        """Test that exceptions during pipeline execution are handled gracefully."""
        # This test will fail - error handling not implemented

        with patch(
            "enviroflow_app.cli.dag.Pipeline.create_full_pipeline"
        ) as mock_pipeline:
            mock_engine = MagicMock()
            mock_engine.execute.side_effect = Exception("API connection failed")
            mock_pipeline.return_value = mock_engine

            from enviroflow_app.pages import data_loading_page

            # Execute pipeline (should not raise exception)
            data_loading_page.run_full_pipeline()

            # Verify error was logged
            error_logs = [
                log
                for log in mock_session_state["execution_log"]
                if log["level"] == "ERROR"
            ]
            assert len(error_logs) > 0

            # Verify last_result shows error status
            assert mock_session_state["last_result"] is not None
            assert mock_session_state["last_result"]["status"] == "error"

    def test_pipeline_running_flag_set_during_execution(
        self, mock_streamlit, mock_session_state
    ):
        """Test that pipeline_running flag is set True during execution and False after."""
        # This test will fail - flag management not implemented

        with patch(
            "enviroflow_app.cli.dag.Pipeline.create_full_pipeline"
        ) as mock_pipeline:
            mock_engine = MagicMock()

            # Track when execute is called
            def mock_execute():
                # At this point, pipeline_running should be True
                assert mock_session_state["pipeline_running"] is True
                return {"status": "success"}

            mock_engine.execute = mock_execute
            mock_pipeline.return_value = mock_engine

            from enviroflow_app.pages import data_loading_page

            # Initial state
            assert mock_session_state["pipeline_running"] is False

            # Execute pipeline
            data_loading_page.run_full_pipeline()

            # Should be reset to False after completion
            assert mock_session_state["pipeline_running"] is False


class TestLogStreaming:
    """Tests for log streaming functionality."""

    def test_stream_log_appends_to_execution_log(
        self, mock_streamlit, mock_session_state
    ):
        """Test that stream_log() properly appends to session state."""
        # Import after patching
        import streamlit as st

        st.session_state = mock_session_state

        # Clear log
        mock_session_state["execution_log"] = []

        # Stream a log message
        stream_log("INFO", "Test Operation", "Test message", {"count": 42})

        # Verify it was added
        assert len(mock_session_state["execution_log"]) == 1

        log_entry = mock_session_state["execution_log"][0]
        assert log_entry["level"] == "INFO"
        assert log_entry["operation"] == "Test Operation"
        assert log_entry["message"] == "Test message"
        assert log_entry["details"]["count"] == 42
        assert isinstance(log_entry["timestamp"], datetime)
