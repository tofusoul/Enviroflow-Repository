"""
Data extraction commands for Enviroflow CLI.

Enhanced extraction commands with MotherDuck-first architecture:

Commands:
- extract trello: Job cards and board data from Trello API
- extract float: Labour hours from Float API
- extract xero-costs: Financial costs from Google Sheets P&L (13,652+ records)
- extract sales: Sales data from Google Sheets P&L (30,996+ records)
- extract legacy: Legacy file sources for backward compatibility

Features:
- MotherDuck Default: All commands save to cloud database by default
- Flexible Output: --output flag supports local, motherduck, or both
- Advanced Data Processing: Excel date conversion, comprehensive column typing
- Data Quality: Null filtering and validation for clean datasets
- Error Handling: Graceful fallbacks and comprehensive logging

Output Options:
- motherduck (default): Save to MotherDuck cloud database only
- local: Save to local parquet files only
- both: Save to both MotherDuck and local files

All commands use the DAG execution system for consistent processing and monitoring.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from ..dag import DAGEngine, Pipeline, Task
from ..operations import extraction_ops

console = Console()
extract_app = typer.Typer(help="Data extraction commands")


@extract_app.command("trello")
def sync_trello(
    output: str = typer.Option(
        "motherduck", help="Output destination: local, motherduck, or both"
    ),
) -> None:
    """
    Extract Trello boards and job cards data.

    Features:
    - Trello API integration: Live board and job card data
    - Job card processing: Complete project tracking information
    - MotherDuck default: Cloud database storage by default
    - Flexible output: Configurable local/cloud destinations

    Output: Saves job cards and board data to MotherDuck by default.
    """
    console.print("🎯 [bold blue]Syncing Trello data...[/bold blue]")

    # Import here to avoid circular imports
    from ..config import OutputDestination, PipelineConfig

    # Parse output destination
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
    config = PipelineConfig.create(destination=destination)

    try:
        # Create a simple DAG with just the Trello extraction task
        engine = DAGEngine()

        trello_task = Task(
            name="sync_trello",
            description="Extract Trello boards and job cards",
            func=extraction_ops.extract_trello_data,
            outputs=["job_cards", "raw_boards"],
        )

        # Set the configuration on the engine for tasks to use
        engine.config = config

        engine.add_task(trello_task)
        results = engine.execute()

        job_cards = results.get("sync_trello.job_cards")
        if job_cards is not None:
            console.print(
                f"✅ [bold green]Trello sync complete![/bold green] Extracted {len(job_cards)} job cards."
            )
        else:
            console.print("⚠️ No job cards data returned from extraction")

    except Exception as e:
        console.print(f"❌ [bold red]Trello sync failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@extract_app.command("float")
def sync_float(
    output: str = typer.Option(
        "motherduck", help="Output destination: local, motherduck, or both"
    ),
) -> None:
    """
    Extract Float labour hours and time tracking data.

    Features:
    - Float API integration: Live labour hours and project time data
    - Time tracking: Comprehensive project labour analytics
    - MotherDuck default: Cloud database storage by default
    - Data processing: Clean time records for project analysis

    Output: Saves labour hours data to MotherDuck by default.
    """
    console.print("⚒️ [bold blue]Syncing Float data...[/bold blue]")

    # Import here to avoid circular imports
    from ..config import OutputDestination, PipelineConfig

    # Parse output destination
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
    config = PipelineConfig.create(destination=destination)

    try:
        engine = DAGEngine()

        float_task = Task(
            name="sync_float",
            description="Extract Float labour hours data",
            func=extraction_ops.extract_float_data,
            outputs=["labour_hours", "raw_float"],
        )

        # Set the configuration on the engine for tasks to use
        engine.config = config

        engine.add_task(float_task)
        results = engine.execute()

        labour_hours = results.get("sync_float.labour_hours")
        if labour_hours is not None:
            console.print(
                f"✅ [bold green]Float sync complete![/bold green] Extracted {len(labour_hours)} labour records."
            )
        else:
            console.print("⚠️ No labour hours data returned from extraction")

    except Exception as e:
        console.print(f"❌ [bold red]Float sync failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@extract_app.command("xero-costs")
def sync_xero_costs(
    output: str = typer.Option(
        "motherduck", help="Output destination: local, motherduck, or both"
    ),
) -> None:
    """
    Extract enhanced Xero costs data from Google Sheets P&L.

    Features:
    - Live Google Sheets integration: 13,652+ cost records (vs legacy 999)
    - Excel date conversion: Serial numbers → Date type (not string)
    - Financial column typing: All monetary fields as Float64
    - Data quality: Null date filtering for clean analysis
    - MotherDuck default: Cloud database storage by default
    - Graceful fallback: Local file backup if Google Sheets unavailable

    Output: Saves to 'xero_costs' table in MotherDuck by default.
    """
    console.print("💰 [bold blue]Syncing Xero costs...[/bold blue]")

    # Import here to avoid circular imports
    from ..config import OutputDestination, PipelineConfig

    # Parse output destination
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
    config = PipelineConfig.create(destination=destination)

    try:
        engine = DAGEngine()

        xero_task = Task(
            name="sync_xero_costs",
            description="Extract Xero costs from Google Sheets",
            func=extraction_ops.extract_xero_costs,
            outputs=["xero_costs", "raw_costs"],
        )

        # Set the configuration on the engine for tasks to use
        engine.config = config

        engine.add_task(xero_task)
        results = engine.execute()

        xero_costs = results.get("sync_xero_costs.xero_costs")
        if xero_costs is not None:
            console.print(
                f"✅ [bold green]Xero costs sync complete![/bold green] Extracted {len(xero_costs)} cost records."
            )
        else:
            console.print("⚠️ No xero costs data returned from extraction")

    except Exception as e:
        console.print(f"❌ [bold red]Xero costs sync failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@extract_app.command("sales")
def sync_sales(
    output: str = typer.Option(
        "motherduck", help="Output destination: local, motherduck, or both"
    ),
) -> None:
    """
    Extract comprehensive sales data from Google Sheets P&L.

    Features:
    - Large dataset: 30,996+ sales records from live Google Sheets
    - Advanced date processing: Excel serial numbers → Date type
    - Comprehensive typing: Financial columns (Debit, Credit, Running Balance,
      Gross, GST, amount) as Float64, text columns as String
    - Data integrity: Null date filtering ensures clean datasets
    - MotherDuck integration: Default cloud database storage
    - Real-time data: Live Google Sheets connectivity for up-to-date sales data

    Output: Saves to 'xero_sales' table in MotherDuck by default.
    """
    console.print("📈 [bold blue]Syncing sales data...[/bold blue]")

    # Import here to avoid circular imports
    from ..config import OutputDestination, PipelineConfig

    # Parse output destination
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
    config = PipelineConfig.create(destination=destination)

    try:
        engine = DAGEngine()

        sales_task = Task(
            name="sync_sales",
            description="Extract sales data from Google Sheets",
            func=extraction_ops.extract_sales_data,
            outputs=["sales_data"],
        )

        # Set the configuration on the engine for tasks to use
        engine.config = config

        engine.add_task(sales_task)
        results = engine.execute()

        sales_data = results.get("sync_sales.sales_data")
        if sales_data is not None:
            console.print(
                f"✅ [bold green]Sales sync complete![/bold green] Extracted {len(sales_data)} sales records."
            )
        else:
            console.print("⚠️ No sales data returned from extraction")

    except Exception as e:
        console.print(f"❌ [bold red]Sales sync failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@extract_app.command("all")
def sync_all_extraction() -> None:
    """Run all extraction operations in parallel."""
    console.print("🚀 [bold blue]Running all extraction operations...[/bold blue]")

    try:
        # Use the predefined extraction pipeline
        engine = Pipeline.create_extraction_pipeline()

        # Execute all extraction tasks
        results = engine.execute()

        console.print("✅ [bold green]All extraction operations complete![/bold green]")

        # Show summary of extracted data
        for task_name, task in engine.tasks.items():
            if task.status.value == "success":
                if f"{task_name}.job_cards" in results:
                    data = results[f"{task_name}.job_cards"]
                    console.print(f"  📊 {task_name}: {len(data)} job cards")
                elif f"{task_name}.labour_hours" in results:
                    data = results[f"{task_name}.labour_hours"]
                    console.print(f"  📊 {task_name}: {len(data)} labour records")
                elif f"{task_name}.xero_costs" in results:
                    data = results[f"{task_name}.xero_costs"]
                    console.print(f"  📊 {task_name}: {len(data)} cost records")
                else:
                    console.print(f"  ✅ {task_name}: completed")

    except Exception as e:
        console.print(f"❌ [bold red]Extraction pipeline failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@extract_app.command("validate")
def validate_extraction(
    tables: Optional[List[str]] = typer.Option(
        None, "--table", help="Specific tables to validate (can be used multiple times)"
    ),
) -> None:
    """Validate extracted data quality."""
    console.print("🔍 [bold blue]Validating extraction outputs...[/bold blue]")

    try:
        from ..operations.validation_ops import validate_job_cards, validate_quotes

        processed_dir = Path("Data/cli_pipeline_data/processed_parquet")

        if not tables:
            tables = ["job_cards", "quotes"]

        all_passed = True

        for table_name in tables:
            file_path = processed_dir / f"{table_name}.parquet"

            if not file_path.exists():
                console.print(f"⚠️ Table file not found: {file_path}")
                continue

            import polars as pl

            df = pl.read_parquet(file_path)

            if table_name == "job_cards":
                result = validate_job_cards(df)
            elif table_name == "quotes":
                result = validate_quotes(df)
            else:
                console.print(f"⚠️ No validation function for table: {table_name}")
                continue

            if result["validation_passed"]:
                console.print(f"✅ {table_name} validation passed")
            else:
                console.print(f"❌ {table_name} validation failed")
                all_passed = False

            # Show warnings and errors
            for warning in result.get("warnings", []):
                console.print(f"  ⚠️ {warning}")

            for error in result.get("errors", []):
                console.print(f"  ❌ {error}")

        if all_passed:
            console.print(
                "✅ [bold green]All extraction validation passed![/bold green]"
            )
        else:
            console.print("❌ [bold red]Some extraction validation failed![/bold red]")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"❌ [bold red]Validation failed:[/bold red] {e}")
        raise typer.Exit(code=1)
