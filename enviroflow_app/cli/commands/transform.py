"""
Data transformation commands for Enviroflow CLI.

Commands for transforming extracted data into business objects using the DAG system.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from ..dag import DAGEngine, Pipeline, Task
from ..operations import transform_ops

console = Console()
transform_app = typer.Typer(help="Data transformation commands")


@transform_app.command("quotes")
def build_quotes() -> None:
    """Build unified quotes table from Xero and Simpro sources."""
    console.print("🔗 [bold blue]Building quotes table...[/bold blue]")

    try:
        engine = DAGEngine()

        quotes_task = Task(
            name="build_quotes",
            description="Build unified quotes table",
            func=transform_ops.build_quotes_table,
            outputs=["quotes"],
        )

        engine.add_task(quotes_task)
        results = engine.execute()

        quotes = results.get("build_quotes.quotes")
        if quotes is not None:
            console.print(
                f"✅ [bold green]Quotes table built![/bold green] Created {len(quotes)} quote records."
            )
        else:
            console.print("⚠️ No quotes data returned from building")

    except Exception as e:
        console.print(f"❌ [bold red]Quotes building failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@transform_app.command("jobs")
def build_jobs() -> None:
    """Build jobs table from job cards and quotes."""
    console.print("🏗️ [bold blue]Building jobs table...[/bold blue]")

    try:
        # This requires job_cards and quotes as inputs
        # We'll load them from files and pass to the operation
        processed_dir = Path("Data/cli_pipeline_data/processed_parquet")

        import polars as pl

        job_cards_path = processed_dir / "job_cards.parquet"
        quotes_path = processed_dir / "quotes.parquet"

        if not job_cards_path.exists():
            console.print(f"❌ Required file not found: {job_cards_path}")
            console.print("Run 'extract trello' first to generate job cards")
            raise typer.Exit(code=1)

        if not quotes_path.exists():
            console.print(f"❌ Required file not found: {quotes_path}")
            console.print("Run 'transform quotes' first to generate quotes table")
            raise typer.Exit(code=1)

        console.print("📖 Loading job cards and quotes...")
        job_cards = pl.read_parquet(job_cards_path)
        quotes = pl.read_parquet(quotes_path)

        # Create and execute task
        engine = DAGEngine()

        def build_jobs_with_data() -> dict:
            return transform_ops.build_jobs_table(job_cards, quotes)

        jobs_task = Task(
            name="build_jobs",
            description="Build jobs table from job cards and quotes",
            func=build_jobs_with_data,
            outputs=["jobs", "job_quote_mapping"],
        )

        engine.add_task(jobs_task)
        results = engine.execute()

        jobs = results.get("build_jobs.jobs")
        if jobs is not None:
            console.print(
                f"✅ [bold green]Jobs table built![/bold green] Created {len(jobs)} job records."
            )
        else:
            console.print("⚠️ No jobs data returned from building")

    except Exception as e:
        console.print(f"❌ [bold red]Jobs building failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@transform_app.command("customers")
def build_customers() -> None:
    """Build customers table from job cards."""
    console.print("👥 [bold blue]Building customers table...[/bold blue]")

    try:
        processed_dir = Path("Data/cli_pipeline_data/processed_parquet")

        import polars as pl

        job_cards_path = processed_dir / "job_cards.parquet"

        if not job_cards_path.exists():
            console.print(f"❌ Required file not found: {job_cards_path}")
            console.print("Run 'extract trello' first to generate job cards")
            raise typer.Exit(code=1)

        console.print("📖 Loading job cards...")
        job_cards = pl.read_parquet(job_cards_path)

        # Create and execute task
        engine = DAGEngine()

        from ..config import PipelineConfig, OutputDestination

        # Get config from main pipeline or create default
        config = PipelineConfig.create(destination=OutputDestination.MOTHERDUCK)

        def build_customers_with_data() -> dict:
            return transform_ops.build_customers_table(job_cards, config)

        customers_task = Task(
            name="build_customers",
            description="Build customers table from job cards",
            func=build_customers_with_data,
            outputs=["customers"],
        )

        engine.add_task(customers_task)
        results = engine.execute()

        customers = results.get("build_customers.customers")
        if customers is not None:
            console.print(
                f"✅ [bold green]Customers table built![/bold green] Created {len(customers)} customer records."
            )
        else:
            console.print("⚠️ No customers data returned from building")

    except Exception as e:
        console.print(f"❌ [bold red]Customers building failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@transform_app.command("add-labour")
def add_labour() -> None:
    """Add labour hours to jobs and create analytics tables."""
    console.print("⚒️ [bold blue]Adding labour hours to jobs...[/bold blue]")

    try:
        processed_dir = Path("Data/cli_pipeline_data/processed_parquet")

        import polars as pl

        # Check required files
        required_files = {
            "jobs": "jobs.parquet",
            "labour_hours": "labour_hours.parquet",
            "quotes": "quotes.parquet",
        }

        loaded_data = {}
        for data_name, file_name in required_files.items():
            file_path = processed_dir / file_name
            if not file_path.exists():
                console.print(f"❌ Required file not found: {file_path}")
                console.print(f"Run the appropriate command to generate {file_name}")
                raise typer.Exit(code=1)

            console.print(f"📖 Loading {data_name}...")
            loaded_data[data_name] = pl.read_parquet(file_path)

        # Create and execute task
        engine = DAGEngine()

        from ..config import PipelineConfig, OutputDestination

        config = PipelineConfig.create(destination=OutputDestination.MOTHERDUCK)

        def add_labour_with_data() -> dict:
            return transform_ops.add_labour_to_jobs(
                loaded_data["jobs"],
                loaded_data["labour_hours"],
                loaded_data["quotes"],
                config,
            )

        labour_task = Task(
            name="add_labour",
            description="Add labour hours to jobs and create analytics",
            func=add_labour_with_data,
            outputs=["jobs_with_hours", "jobs_for_analytics"],
        )

        engine.add_task(labour_task)
        results = engine.execute()

        jobs_with_hours = results.get("add_labour.jobs_with_hours")
        if jobs_with_hours is not None:
            console.print(
                f"✅ [bold green]Labour integration complete![/bold green] Enhanced {len(jobs_with_hours)} job records."
            )
        else:
            console.print("⚠️ No jobs with hours data returned")

    except Exception as e:
        console.print(f"❌ [bold red]Labour integration failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@transform_app.command("projects")
def build_projects() -> None:
    """Build projects table from jobs with labour hours."""
    console.print("🏗️ [bold blue]Building projects table...[/bold blue]")

    try:
        processed_dir = Path("Data/cli_pipeline_data/processed_parquet")

        import polars as pl

        # Check required files
        required_files = {
            "jobs_with_hours": "jobs_with_hours.parquet",
            "quotes": "quotes.parquet",
        }

        loaded_data = {}
        for data_name, file_name in required_files.items():
            file_path = processed_dir / file_name
            if not file_path.exists():
                console.print(f"❌ Required file not found: {file_path}")
                console.print(f"Run the appropriate command to generate {file_name}")
                raise typer.Exit(code=1)

            console.print(f"📖 Loading {data_name}...")
            loaded_data[data_name] = pl.read_parquet(file_path)

        # Create and execute task
        engine = DAGEngine()

        def build_projects_with_data() -> dict:
            return transform_ops.build_projects_table(
                loaded_data["jobs_with_hours"], loaded_data["quotes"]
            )

        projects_task = Task(
            name="build_projects",
            description="Build projects table from jobs with labour",
            func=build_projects_with_data,
            outputs=["projects"],
        )

        engine.add_task(projects_task)
        results = engine.execute()

        projects = results.get("build_projects.projects")
        if projects is not None:
            console.print(
                f"✅ [bold green]Projects table built![/bold green] Created {len(projects)} project records."
            )
        else:
            console.print("⚠️ No projects data returned from building")

    except Exception as e:
        console.print(f"❌ [bold red]Projects building failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@transform_app.command("projects-analytics")
def build_projects_analytics() -> None:
    """Build enriched projects table for analytics with financial data."""
    console.print("📊 [bold blue]Building projects analytics table...[/bold blue]")

    try:
        processed_dir = Path("Data/cli_pipeline_data/processed_parquet")

        import polars as pl

        # Check required files
        required_files = {
            "projects": "projects.parquet",
            "jobs_analytics": "jobs_for_analytics.parquet",
            "quotes": "quotes.parquet",
            "labour_hours": "labour_hours.parquet",
            "costs": "xero_costs.parquet",
        }

        loaded_data = {}
        for data_name, file_name in required_files.items():
            file_path = processed_dir / file_name
            if not file_path.exists():
                console.print(f"❌ Required file not found: {file_path}")
                console.print(f"Run the appropriate command to generate {file_name}")
                raise typer.Exit(code=1)

            console.print(f"📖 Loading {data_name}...")
            loaded_data[data_name] = pl.read_parquet(file_path)

        # Create and execute task
        engine = DAGEngine()

        def build_analytics_with_data() -> dict:
            return transform_ops.build_projects_analytics(
                loaded_data["projects"],
                loaded_data["jobs_analytics"],
                loaded_data["quotes"],
                loaded_data["labour_hours"],
                loaded_data["costs"],
            )

        analytics_task = Task(
            name="build_projects_analytics",
            description="Build enriched projects for analytics",
            func=build_analytics_with_data,
            outputs=["projects_for_analytics"],
        )

        engine.add_task(analytics_task)
        results = engine.execute()

        projects_analytics = results.get(
            "build_projects_analytics.projects_for_analytics"
        )
        if projects_analytics is not None:
            console.print(
                f"✅ [bold green]Projects analytics built![/bold green] Enhanced {len(projects_analytics)} project records."
            )

            # Show financial summary
            if "total_quote_value" in projects_analytics.columns:
                total_value = projects_analytics["total_quote_value"].sum()
                console.print(f"📊 Total project value: ${total_value:,.2f}")

            if "gross_profit" in projects_analytics.columns:
                total_profit = projects_analytics["gross_profit"].sum()
                console.print(f"📊 Total gross profit: ${total_profit:,.2f}")
        else:
            console.print("⚠️ No projects analytics data returned")

    except Exception as e:
        console.print(
            f"❌ [bold red]Projects analytics building failed:[/bold red] {e}"
        )
        raise typer.Exit(code=1)


@transform_app.command("all")
def run_all_transformations() -> None:
    """Run all transformation operations in dependency order."""
    console.print("🚀 [bold blue]Running all transformation operations...[/bold blue]")

    try:
        # Use the predefined transformation pipeline
        engine = Pipeline.create_transform_pipeline()

        # Execute the full transformation pipeline
        results = engine.execute()

        console.print(
            "✅ [bold green]All transformation operations complete![/bold green]"
        )

        # Show summary of created tables
        key_outputs = [
            ("build_quotes.quotes", "quotes"),
            ("build_jobs.jobs", "jobs"),
            ("build_customers.customers", "customers"),
            ("add_labour.jobs_with_hours", "jobs with hours"),
            ("build_projects.projects", "projects"),
            ("build_projects_analytics.projects_for_analytics", "analytics projects"),
        ]

        for output_key, description in key_outputs:
            if output_key in results:
                data = results[output_key]
                console.print(f"  📊 {description}: {len(data)} records")

    except Exception as e:
        console.print(f"❌ [bold red]Transformation pipeline failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@transform_app.command("validate")
def validate_transformations(
    tables: Optional[List[str]] = typer.Option(
        None, "--table", help="Specific tables to validate (can be used multiple times)"
    ),
) -> None:
    """Validate transformation outputs."""
    console.print("🔍 [bold blue]Validating transformation outputs...[/bold blue]")

    try:
        from ..operations.validation_ops import run_full_validation_suite

        processed_dir = Path("Data/cli_pipeline_data/processed_parquet")

        if not tables:
            # Run full validation suite
            results = run_full_validation_suite(processed_dir)

            if results["overall_passed"]:
                console.print(
                    "✅ [bold green]All transformation validation passed![/bold green]"
                )
            else:
                console.print(
                    "❌ [bold red]Some transformation validation failed![/bold red]"
                )
                raise typer.Exit(code=1)
        else:
            # Validate specific tables
            for table_name in tables:
                console.print(f"🔍 Validating {table_name}...")
                # Add specific table validation logic here as needed

    except Exception as e:
        console.print(f"❌ [bold red]Validation failed:[/bold red] {e}")
        raise typer.Exit(code=1)
