"""
Pipeline definitions for Enviroflow ELT operations.

Contains predefined pipeline configurations and factory functions
for creating common DAG patterns.
"""

from __future__ import annotations

from typing import Dict, List

from .engine import DAGEngine
from .task import Task


class Pipeline:
    """
    Factory class for creating predefined DAG pipelines.

    Provides convenient methods for creating common pipeline patterns
    and configurations used in the Enviroflow ELT process.
    """

    @staticmethod
    def create_extraction_pipeline() -> DAGEngine:
        """
        Create a pipeline for data extraction operations.

        Includes tasks for:
        - sync-trello
        - sync-float
        - sync-xero-costs
        """
        from ..operations.extraction_ops import (
            extract_float_data,
            extract_trello_data,
            extract_xero_costs,
        )

        engine = DAGEngine()

        # Define extraction tasks (no dependencies between them)
        tasks = [
            Task(
                name="sync_trello",
                description="Extract Trello boards and job cards",
                func=extract_trello_data,
                outputs=["job_cards"],
            ),
            Task(
                name="sync_float",
                description="Extract Float labour hours data",
                func=extract_float_data,
                outputs=["labour_hours"],
            ),
            Task(
                name="sync_xero_costs",
                description="Extract Xero costs from Google Sheets",
                func=extract_xero_costs,
                outputs=["xero_costs"],
            ),
        ]

        engine.add_tasks(tasks)
        return engine

    @staticmethod
    def create_transform_pipeline() -> DAGEngine:
        """
        Create a pipeline for data transformation operations.

        Includes tasks for:
        - build-quotes (depends on extraction)
        - build-jobs (depends on job_cards + quotes)
        - build-customers (depends on job_cards)
        - add-labour (depends on jobs + labour_hours)
        - build-projects (depends on jobs_with_labour)
        - build-projects-analytics (depends on all data)
        """
        from ..operations.transform_ops import (
            add_labour_to_jobs,
            build_customers_table,
            build_jobs_table,
            build_projects_analytics,
            build_projects_table,
            build_quotes_table,
        )

        engine = DAGEngine()

        # Define transformation tasks with dependencies
        tasks = [
            Task(
                name="build_quotes",
                description="Build unified quotes table from Xero and Simpro",
                func=build_quotes_table,
                inputs={
                    # No inputs - will use download_production_quotes() fallback
                },
                outputs=["quotes"],
            ),
            Task(
                name="build_jobs",
                description="Transform job cards into jobs table",
                func=build_jobs_table,
                inputs={
                    "job_cards": "sync_trello.job_cards",
                    "quotes": "build_quotes.quotes",
                },
                outputs=["jobs", "job_quote_mapping"],
            ),
            Task(
                name="build_customers",
                description="Extract unique customers from job cards",
                func=build_customers_table,
                inputs={"job_cards": "sync_trello.job_cards"},
                outputs=["customers"],
            ),
            Task(
                name="add_labour",
                description="Add labour hours to jobs",
                func=add_labour_to_jobs,
                inputs={
                    "jobs": "build_jobs.jobs",
                    "labour_hours": "sync_float.labour_hours",
                    "quotes": "build_quotes.quotes",
                },
                outputs=["jobs_with_hours", "jobs_for_analytics"],
            ),
            Task(
                name="build_projects",
                description="Build projects table from jobs with labour",
                func=build_projects_table,
                inputs={
                    "jobs_with_hours": "add_labour.jobs_with_hours",
                    "quotes": "build_quotes.quotes",
                },
                outputs=["projects"],
            ),
            Task(
                name="build_projects_analytics",
                description="Build enriched projects for analytics",
                func=build_projects_analytics,
                inputs={
                    "projects": "build_projects.projects",
                    "jobs_analytics": "add_labour.jobs_for_analytics",
                    "quotes": "build_quotes.quotes",
                    "labour_hours": "sync_float.labour_hours",
                    "costs": "sync_xero_costs.xero_costs",
                },
                outputs=["projects_for_analytics"],
            ),
        ]

        engine.add_tasks(tasks)
        return engine

    @staticmethod
    def create_full_pipeline() -> DAGEngine:
        """
        Create the complete ELT pipeline.

        Combines extraction and transformation pipelines into a single DAG.
        """
        # Start with extraction pipeline
        extraction_engine = Pipeline.create_extraction_pipeline()
        transform_engine = Pipeline.create_transform_pipeline()

        # Combine both engines
        full_engine = DAGEngine()

        # Add all tasks from both pipelines
        full_engine.tasks.update(extraction_engine.tasks)
        full_engine.tasks.update(transform_engine.tasks)

        return full_engine

    @staticmethod
    def create_custom_pipeline(task_configs: List[Dict]) -> DAGEngine:
        """
        Create a custom pipeline from configuration.

        Args:
            task_configs: List of task configuration dictionaries

        Example:
            task_configs = [
                {
                    "name": "extract_data",
                    "func": my_extract_function,
                    "description": "Extract raw data",
                    "outputs": ["raw_data"]
                },
                {
                    "name": "transform_data",
                    "func": my_transform_function,
                    "description": "Transform data",
                    "inputs": {"data": "extract_data.raw_data"},
                    "outputs": ["clean_data"]
                }
            ]
        """
        engine = DAGEngine()

        for config in task_configs:
            task = Task(
                name=config["name"],
                func=config["func"],
                description=config.get("description", ""),
                inputs=config.get("inputs", {}),
                outputs=config.get("outputs", []),
            )
            engine.add_task(task)

        return engine


# Common pipeline configurations
PIPELINE_CONFIGS = {
    "extraction_only": {
        "description": "Extract data from all sources",
        "tasks": ["sync_trello", "sync_float", "sync_xero_costs"],
    },
    "quotes_pipeline": {
        "description": "Build quotes table",
        "tasks": ["build_quotes"],
    },
    "jobs_pipeline": {
        "description": "Build jobs with quotes",
        "tasks": ["sync_trello", "build_quotes", "build_jobs"],
    },
    "analytics_pipeline": {
        "description": "Full analytics pipeline",
        "tasks": ["build_projects_analytics"],  # Will include all dependencies
    },
    "full_pipeline": {
        "description": "Complete ELT pipeline",
        "tasks": None,  # Execute all tasks
    },
}


def get_pipeline_config(pipeline_name: str) -> Dict:
    """Get configuration for a named pipeline."""
    if pipeline_name not in PIPELINE_CONFIGS:
        available = list(PIPELINE_CONFIGS.keys())
        raise ValueError(f"Unknown pipeline '{pipeline_name}'. Available: {available}")

    return PIPELINE_CONFIGS[pipeline_name]
