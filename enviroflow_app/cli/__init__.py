"""
Enviroflow CLI package.

Modern, DAG-based command-line interface for the Enviroflow ELT pipeline.

This package provides:
- Custom DAG orchestration system
- Modular command structure
- Type-annotated operations
- Comprehensive validation
- Rich console output
"""


# Import app only when needed to avoid circular import warnings
def get_app():
    """Get the CLI app instance."""
    from .main import app

    return app


__all__ = ["get_app"]
