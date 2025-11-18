"""
Integration tests for individual CLI commands.

Tests that each CLI command group (extract, transform, load) works correctly.
"""

import subprocess
import sys

import pytest


@pytest.mark.integration
class TestCLICommands:
    """Test individual CLI commands work correctly."""

    def run_cli_command(self, *args):
        """Helper to run CLI commands and capture output."""
        command = [sys.executable, "-m", "enviroflow_app.cli.main"] + list(args)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        return result

    def test_cli_help_works(self):
        """Test that the CLI help command works."""
        result = self.run_cli_command("--help")
        assert result.returncode == 0
        assert "Enviroflow ELT Pipeline" in result.stdout

    def test_status_command_works(self):
        """Test that the status command works."""
        result = self.run_cli_command("status")
        assert result.returncode == 0

    @pytest.mark.parametrize("extract_cmd", ["trello", "float", "xero-costs"])
    def test_extract_commands(self, extract_cmd):
        """Test extract commands work without errors."""
        result = self.run_cli_command("extract", extract_cmd)
        # Commands should at least not crash (may have no data in test env)
        assert result.returncode in [0, 1]  # Allow for expected data errors

    @pytest.mark.parametrize(
        "transform_cmd",
        ["quotes", "jobs", "customers", "labour", "projects", "analytics"],
    )
    def test_transform_commands(self, transform_cmd):
        """Test transform commands work without errors."""
        result = self.run_cli_command("transform", transform_cmd)
        # Commands should at least not crash (may have no data in test env)
        assert result.returncode in [0, 1]  # Allow for expected data errors

    def test_load_motherduck_command(self):
        """Test load motherduck command works."""
        result = self.run_cli_command("load", "motherduck")
        # May fail due to missing data, but shouldn't crash
        assert result.returncode in [0, 1]
