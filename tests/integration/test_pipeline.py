"""
Integration tests for the main Enviroflow CLI pipeline.

These tests execute the pipeline commands to ensure they run end-to-end
without errors.
"""

import subprocess
import sys

import pytest


@pytest.mark.integration
def test_run_all_pipeline_successfully():
    """
    Tests that the `run-all` command completes successfully.
    """
    command = [
        sys.executable,
        "-m",
        "enviroflow_app.cli.main",
        "run-all",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,  # Don't raise exception on non-zero exit
    )

    # For debugging, print stdout/stderr if the test fails
    if result.returncode != 0:
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)

    assert result.returncode == 0, "The 'run-all' pipeline command failed."
    assert "Pipeline completed successfully!" in result.stdout
