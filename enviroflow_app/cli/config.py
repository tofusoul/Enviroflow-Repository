"""
Configuration classes for CLI pipeline operations.

Handles output destinations, authentication, and pipeline settings.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import os
import streamlit as st
from rich.console import Console

console = Console()


class OutputDestination(Enum):
    """Enumeration of supported output destinations."""

    LOCAL = "local"
    MOTHERDUCK = "motherduck"
    BOTH = "both"


@dataclass
class OutputConfig:
    """Configuration for pipeline output destinations."""

    destination: OutputDestination
    local_dir: Path = Path("Data/cli_pipeline_data/processed_parquet")
    motherduck_db: str = "enviroflow"
    motherduck_token: Optional[str] = None

    def __post_init__(self):
        """Initialize MotherDuck token if needed."""
        if self.destination in [OutputDestination.MOTHERDUCK, OutputDestination.BOTH]:
            if not self.motherduck_token:
                self.motherduck_token = self._get_motherduck_token()

    def _get_motherduck_token(self) -> str:
        """Get MotherDuck token from secrets or environment."""
        # Try Streamlit secrets first
        secrets_path = Path(".streamlit/secrets.toml")
        if secrets_path.exists():
            try:
                # Force streamlit to read secrets
                _ = st.secrets
                token = st.secrets["motherduck"]["token"]
                console.print("✅ Using MotherDuck token from Streamlit secrets")
                return token
            except (KeyError, Exception):
                pass

        # Try environment variable
        token = os.getenv("MOTHER_DUCK")
        if token:
            console.print("✅ Using MotherDuck token from environment")
            return token

        # No token found
        raise ValueError(
            "No MotherDuck token found. Please ensure .streamlit/secrets.toml exists "
            "with motherduck.token or set MOTHER_DUCK environment variable"
        )

    @property
    def save_local(self) -> bool:
        """Whether to save to local files."""
        return self.destination in [OutputDestination.LOCAL, OutputDestination.BOTH]

    @property
    def save_motherduck(self) -> bool:
        """Whether to save to MotherDuck."""
        return self.destination in [
            OutputDestination.MOTHERDUCK,
            OutputDestination.BOTH,
        ]

    def ensure_local_dir(self):
        """Ensure local output directory exists."""
        if self.save_local:
            self.local_dir.mkdir(parents=True, exist_ok=True)

    def get_motherduck_connection(self):
        """Get MotherDuck connection if needed."""
        if self.save_motherduck:
            if not self.motherduck_token:
                raise ValueError("MotherDuck token is required but not available")
            from enviroflow_app.elt.motherduck.md import MotherDuck

            return MotherDuck(db_name=self.motherduck_db, token=self.motherduck_token)
        return None


@dataclass
class PipelineConfig:
    """Main configuration for pipeline execution."""

    output: OutputConfig
    validate: bool = True
    pipeline_type: str = "full"

    @classmethod
    def create(
        cls,
        destination: OutputDestination = OutputDestination.MOTHERDUCK,
        validate: bool = True,
        pipeline_type: str = "full",
    ) -> "PipelineConfig":
        """Create pipeline configuration with specified options."""
        output_config = OutputConfig(destination=destination)
        return cls(output=output_config, validate=validate, pipeline_type=pipeline_type)
