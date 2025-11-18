"""
Main CLI entry point for Enviroflow ELT pipeline.

This is the primary command-line interface with DAG-based pipeline orchestration.
This replaces the original cli.py with a more modular, maintainable structure.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .commands.extract import extract_app
from .commands.load import load_app
from .commands.transform import transform_app
from .config import OutputDestination, PipelineConfig
from .dag import Pipeline

console = Console()

# Main CLI application
app = typer.Typer(
    help="Enviroflow ELT Pipeline - Data extraction, transformation, and loading for business analytics"
)

# Add sub-applications
app.add_typer(extract_app, name="extract", help="Data extraction commands")
app.add_typer(transform_app, name="transform", help="Data transformation commands")
app.add_typer(load_app, name="load", help="Data loading and persistence commands")


@app.command()
def run_all(
    pipeline: str = typer.Option(
        "full", help="Pipeline to run: extraction, transform, or full"
    ),
    validate: bool = typer.Option(True, help="Run validation after completion"),
    output: str = typer.Option(
        "motherduck", help="Output destination: local, motherduck, or both"
    ),
) -> None:
    """
    Run the complete ELT pipeline or specific pipeline segments.

    By default, outputs are saved to MotherDuck. Use --output=local for local files only,
    or --output=both to save to both destinations.
    """
    console.print("🚀 [bold blue]Starting Enviroflow ELT Pipeline...[/bold blue]")

    # Determine output destination
    if output == "both":
        destination = OutputDestination.BOTH
        console.print(
            "💾 [bold yellow]Output mode: Both local files and MotherDuck[/bold yellow]"
        )
    elif output == "local":
        destination = OutputDestination.LOCAL
        console.print("💾 [bold blue]Output mode: Local files only[/bold blue]")
    elif output == "motherduck":
        destination = OutputDestination.MOTHERDUCK
        console.print("💾 [bold green]Output mode: MotherDuck only[/bold green]")
    else:
        console.print(f"❌ Invalid output destination: {output}")
        console.print("Valid options: local, motherduck, both")
        raise typer.Exit(code=1)

    # Create pipeline configuration
    config = PipelineConfig.create(
        destination=destination, validate=validate, pipeline_type=pipeline
    )

    try:
        # Create appropriate pipeline based on selection
        if config.pipeline_type == "extraction":
            console.print("📥 Running extraction pipeline only...")
            engine = Pipeline.create_extraction_pipeline()
        elif config.pipeline_type == "transform":
            console.print("🔄 Running transformation pipeline only...")
            engine = Pipeline.create_transform_pipeline()
        elif config.pipeline_type == "full":
            console.print("🎯 Running complete ELT pipeline...")
            engine = Pipeline.create_full_pipeline()
        else:
            console.print(f"❌ Unknown pipeline type: {config.pipeline_type}")
            console.print("Available options: extraction, transform, full")
            raise typer.Exit(code=1)

        # Set the configuration on the engine for tasks to use
        engine.config = config

        # Show pipeline structure
        console.print("\n📋 [bold]Pipeline Structure:[/bold]")
        engine.visualize()

        # Execute the pipeline
        console.print("\n🚀 [bold]Executing Pipeline:[/bold]")
        results = engine.execute()

        # Show execution summary
        console.print("\n📊 [bold blue]Execution Summary:[/bold blue]")

        successful_tasks = [
            name
            for name, task in engine.tasks.items()
            if task.status.value == "success"
        ]
        failed_tasks = [
            name for name, task in engine.tasks.items() if task.status.value == "failed"
        ]

        summary_table = Table(title="Pipeline Results")
        summary_table.add_column("Task", style="cyan")
        summary_table.add_column("Status", style="bold")
        summary_table.add_column("Records", justify="right")
        summary_table.add_column("Description")

        for task_name, task in engine.tasks.items():
            if task.status.value == "success":
                status = "✅ SUCCESS"
                style = "green"
            elif task.status.value == "failed":
                status = "❌ FAILED"
                style = "red"
            else:
                status = f"⚪ {task.status.value.upper()}"
                style = "yellow"

            # Try to get record count from results
            record_count = "—"
            for output in task.outputs:
                result_key = f"{task_name}.{output}"
                if result_key in results:
                    data = results[result_key]
                    if hasattr(data, "__len__"):
                        record_count = f"{len(data):,}"
                        break

            summary_table.add_row(
                task_name,
                f"[{style}]{status}[/{style}]",
                record_count,
                task.description,
            )

        console.print(summary_table)

        # Overall status
        if failed_tasks:
            console.print("\n❌ [bold red]Pipeline completed with errors![/bold red]")
            console.print(f"Failed tasks: {', '.join(failed_tasks)}")
            raise typer.Exit(code=1)
        else:
            console.print(
                "\n🎉 [bold green]Pipeline completed successfully![/bold green]"
            )
            console.print(f"✅ All {len(successful_tasks)} tasks completed")

        # Run validation if requested
        if validate and pipeline in ["transform", "full"]:
            console.print("\n🔍 [bold blue]Running validation suite...[/bold blue]")

            try:
                from .operations.validation_ops import run_full_validation_suite

                processed_dir = Path("Data/cli_pipeline_data/processed_parquet")
                validation_results = run_full_validation_suite(processed_dir)

                if validation_results["overall_passed"]:
                    console.print(
                        "✅ [bold green]All validation checks passed![/bold green]"
                    )
                else:
                    console.print(
                        "⚠️ [bold yellow]Some validation checks failed[/bold yellow]"
                    )
                    console.print(
                        f"Total errors: {validation_results['summary']['total_errors']}"
                    )
                    console.print(
                        f"Total warnings: {validation_results['summary']['total_warnings']}"
                    )

                    # Print details
                    for validation_name, result in validation_results[
                        "validations"
                    ].items():
                        if result.get("errors"):
                            console.print(
                                f"\n❌ Errors in [bold red]{validation_name}[/bold red]:"
                            )
                            for error in result["errors"]:
                                console.print(f"  - {error}")
                        if result.get("warnings"):
                            console.print(
                                f"\n⚠️ Warnings in [bold yellow]{validation_name}[/bold yellow]:"
                            )
                            for warning in result["warnings"]:
                                console.print(f"  - {warning}")

            except Exception as e:
                console.print(f"⚠️ Validation failed: {e}")

        # Display output location based on configuration
        if config.output.destination == OutputDestination.MOTHERDUCK:
            console.print(
                f"\n💾 [bold]Output Location:[/bold] MotherDuck database '{config.output.motherduck_db}'"
            )
        elif config.output.destination == OutputDestination.LOCAL:
            console.print(
                f"\n💾 [bold]Output Location:[/bold] {config.output.local_dir}"
            )
        elif config.output.destination == OutputDestination.BOTH:
            console.print("\n💾 [bold]Output Locations:[/bold]")
            console.print(f"  • MotherDuck database '{config.output.motherduck_db}'")
            console.print(f"  • Local directory: {config.output.local_dir}")

    except Exception as e:
        console.print(f"\n❌ [bold red]Pipeline execution failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def status() -> None:
    """Show current status of the pipeline and data files."""
    console.print("📊 [bold blue]Enviroflow Pipeline Status[/bold blue]")

    # Show pipeline data status using the load command
    from .commands.load import show_data_status

    show_data_status()

    # Check for any running processes or locks
    console.print("\n🔧 [bold]System Status:[/bold]")

    # Check directories
    dirs_to_check = [
        ("Raw JSON", "Data/cli_pipeline_data/raw_json"),
        ("Processed Parquet", "Data/cli_pipeline_data/processed_parquet"),
        ("P&L Data", "pnl_data"),
    ]

    for name, path in dirs_to_check:
        dir_path = Path(path)
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*")))
            console.print(f"  ✅ {name:<20} {file_count:>3} files")
        else:
            console.print(f"  ⚫ {name:<20} {'—':>3} (not found)")

    # Check configuration
    console.print("\n⚙️ [bold]Configuration:[/bold]")

    config_files = [
        (".streamlit/secrets.toml", "Streamlit secrets"),
        ("pyproject.toml", "Poetry configuration"),
        ("enviroflow_app/config.py", "App configuration"),
    ]

    for file_path, description in config_files:
        if Path(file_path).exists():
            console.print(f"  ✅ {description}")
        else:
            console.print(f"  ⚫ {description} (not found)")


@app.command()
def validate(
    pipeline_stage: Optional[str] = typer.Argument(
        None, help="Stage to validate: extraction, transform, or all"
    ),
    table: Optional[str] = typer.Option(None, help="Specific table to validate"),
) -> None:
    """Run validation checks on pipeline data."""
    console.print("🔍 [bold blue]Running Pipeline Validation[/bold blue]")

    try:
        if pipeline_stage is None:
            pipeline_stage = "all"

        if pipeline_stage in ["extraction", "all"]:
            console.print("\n📥 [bold]Extraction Validation:[/bold]")
            from .commands.extract import validate_extraction

            validate_extraction([table] if table else None)

        if pipeline_stage in ["transform", "all"]:
            console.print("\n🔄 [bold]Transformation Validation:[/bold]")
            from .commands.transform import validate_transformations

            validate_transformations([table] if table else None)

        console.print("\n✅ [bold green]Validation complete![/bold green]")

    except typer.Exit:
        # Re-raise typer exits (validation failures)
        raise
    except Exception as e:
        console.print(f"❌ [bold red]Validation error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def dag_info(
    pipeline: str = typer.Option(
        "full", help="Pipeline to analyze: extraction, transform, or full"
    ),
) -> None:
    """Show DAG structure and dependencies for a pipeline."""
    console.print(f"🔍 [bold blue]DAG Information: {pipeline} pipeline[/bold blue]")

    try:
        # Create the requested pipeline
        if pipeline == "extraction":
            engine = Pipeline.create_extraction_pipeline()
        elif pipeline == "transform":
            engine = Pipeline.create_transform_pipeline()
        elif pipeline == "full":
            engine = Pipeline.create_full_pipeline()
        else:
            console.print(f"❌ Unknown pipeline: {pipeline}")
            console.print("Available options: extraction, transform, full")
            raise typer.Exit(code=1)

        # Validate the DAG
        console.print("\n🔧 [bold]DAG Validation:[/bold]")
        try:
            engine.validate()
            console.print("✅ DAG is valid - no cycles or missing dependencies")
        except Exception as e:
            console.print(f"❌ DAG validation failed: {e}")
            raise typer.Exit(code=1)

        # Show execution order
        console.print("\n📋 [bold]Execution Order:[/bold]")
        execution_order = engine._topological_sort()
        for i, task_name in enumerate(execution_order, 1):
            task = engine.tasks[task_name]
            deps = list(task.dependencies)
            dep_str = (
                f" (depends on: {', '.join(deps)})" if deps else " (no dependencies)"
            )
            console.print(f"  {i:>2}. {task_name}{dep_str}")

        # Show task details
        console.print("\n📝 [bold]Task Details:[/bold]")
        task_table = Table()
        task_table.add_column("Task", style="cyan")
        task_table.add_column("Dependencies", style="yellow")
        task_table.add_column("Outputs", style="green")
        task_table.add_column("Description")

        for task_name in execution_order:
            task = engine.tasks[task_name]
            deps = ", ".join(task.dependencies) if task.dependencies else "—"
            outputs = ", ".join(task.outputs) if task.outputs else "—"

            task_table.add_row(task_name, deps, outputs, task.description)

        console.print(task_table)

        # Show statistics
        console.print("\n📊 [bold]Pipeline Statistics:[/bold]")
        stats_panel = Panel(
            f"""
Total Tasks: {len(engine.tasks)}
Tasks with Dependencies: {len([t for t in engine.tasks.values() if t.dependencies])}
Root Tasks (no deps): {len([t for t in engine.tasks.values() if not t.dependencies])}
Leaf Tasks (no dependents): {len(execution_order) - len(set().union(*[t.dependencies for t in engine.tasks.values()]))}
        """.strip()
        )
        console.print(stats_panel)

    except Exception as e:
        console.print(f"❌ [bold red]DAG analysis failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Show version information."""
    console.print("🏠 [bold blue]Enviroflow ELT Pipeline[/bold blue]")

    version_info = Panel("""
[bold]Enviroflow CLI Pipeline[/bold]
Version: 2.0.0 (DAG-based architecture)
Date: August 2025

[bold]Features:[/bold]
• Custom DAG orchestration system
• Modular command structure
• Type-annotated codebase
• Comprehensive validation suite
• Rich console output

[bold]Pipeline Stages:[/bold]
• Extract: Trello, Float, Xero/Google Sheets
• Transform: Quotes, Jobs, Customers, Labour, Projects, Analytics
• Load: File management, backup/restore, export

[bold]Directories:[/bold]
• Raw JSON: Data/cli_pipeline_data/raw_json/
• Processed: Data/cli_pipeline_data/processed_parquet/
• Documentation: docs/Pipeline_DAG_Specification.md
    """)

    console.print(version_info)


if __name__ == "__main__":
    app()
