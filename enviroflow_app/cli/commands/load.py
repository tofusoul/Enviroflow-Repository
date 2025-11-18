"""
Load/save commands for Enviroflow CLI.

Commands for managing data persistence and file operations.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()
load_app = typer.Typer(help="Data loading and persistence commands")


@load_app.command("status")
def show_data_status() -> None:
    """Show status of all pipeline data files."""
    console.print("📊 [bold blue]Pipeline Data Status[/bold blue]")

    processed_dir = Path("Data/cli_pipeline_data/processed_parquet")
    raw_dir = Path("Data/cli_pipeline_data/raw_json")

    # Expected pipeline files in order
    pipeline_files = [
        # Extraction outputs
        ("job_cards.parquet", "Job cards from Trello"),
        ("labour_hours.parquet", "Labour hours from Float"),
        ("xero_costs.parquet", "Costs from Xero/Google Sheets"),
        # Transformation outputs
        ("quotes.parquet", "Unified quotes table"),
        ("jobs.parquet", "Jobs table"),
        ("customers.parquet", "Customers table"),
        ("jobs_with_hours.parquet", "Jobs with labour hours"),
        ("projects.parquet", "Projects table"),
        ("projects_for_analytics.parquet", "Analytics projects"),
        # Debug/mapping tables
        ("job_quote_mapping.parquet", "Job-to-quote mapping"),
    ]

    console.print("\n📁 [bold]Processed Data Files:[/bold]")
    total_files = len(pipeline_files)
    existing_files = 0

    for file_name, description in pipeline_files:
        file_path = processed_dir / file_name
        if file_path.exists():
            try:
                import polars as pl

                df = pl.read_parquet(file_path)
                file_size = file_path.stat().st_size
                size_mb = file_size / (1024 * 1024)

                console.print(
                    f"  ✅ {file_name:<30} {len(df):>8,} rows  {size_mb:>6.1f}MB  {description}"
                )
                existing_files += 1
            except Exception as e:
                console.print(
                    f"  ❌ {file_name:<30} {'ERROR':>8}  {'---':>6}     {description} - {e}"
                )
        else:
            console.print(
                f"  ⚫ {file_name:<30} {'MISSING':>8}  {'---':>6}     {description}"
            )

    # Raw data files
    console.print("\n📁 [bold]Raw Data Files:[/bold]")
    raw_files = list(raw_dir.glob("*.json")) if raw_dir.exists() else []

    if raw_files:
        for raw_file in sorted(raw_files):
            file_size = raw_file.stat().st_size
            size_mb = file_size / (1024 * 1024)
            console.print(f"  📄 {raw_file.name:<30} {'JSON':>8}  {size_mb:>6.1f}MB")
    else:
        console.print("  ⚫ No raw data files found")

    # Summary
    completion_pct = (existing_files / total_files) * 100
    console.print(
        f"\n📊 [bold]Pipeline Completion:[/bold] {existing_files}/{total_files} files ({completion_pct:.1f}%)"
    )

    if completion_pct == 100:
        console.print("🎉 [bold green]Pipeline is complete![/bold green]")
    elif completion_pct >= 50:
        console.print("🔄 [bold yellow]Pipeline is partially complete[/bold yellow]")
    else:
        console.print("🚀 [bold blue]Pipeline is just getting started[/bold blue]")


@load_app.command("clean")
def clean_data(
    data_type: Optional[str] = typer.Option(
        None, help="Type of data to clean: processed, raw, or all"
    ),
    confirm: bool = typer.Option(False, help="Skip confirmation prompt"),
) -> None:
    """Clean pipeline data files."""

    if data_type is None:
        data_type = typer.prompt("What data would you like to clean?", type=str)

        if data_type not in ["processed", "raw", "all"]:
            console.print("❌ Invalid data type. Choose: processed, raw, or all")
            return

    processed_dir = Path("Data/cli_pipeline_data/processed_parquet")
    raw_dir = Path("Data/cli_pipeline_data/raw_json")

    dirs_to_clean = []
    if data_type in ["processed", "all"]:
        dirs_to_clean.append(("Processed data", processed_dir))
    if data_type in ["raw", "all"]:
        dirs_to_clean.append(("Raw data", raw_dir))

    if not dirs_to_clean:
        console.print("❌ No data type specified for cleaning")
        return

    # Show what will be deleted
    console.print("🗑️ [bold yellow]The following will be deleted:[/bold yellow]")
    total_files = 0

    for dir_name, dir_path in dirs_to_clean:
        if dir_path.exists():
            files = list(dir_path.glob("*"))
            console.print(f"  📁 {dir_name}: {len(files)} files in {dir_path}")
            total_files += len(files)
        else:
            console.print(f"  📁 {dir_name}: directory doesn't exist")

    if total_files == 0:
        console.print("✅ No files to clean")
        return

    # Confirm deletion
    if not confirm:
        confirmed = typer.confirm(
            f"Are you sure you want to delete {total_files} files?"
        )
        if not confirmed:
            console.print("❌ Cleaning cancelled")
            return

    # Perform deletion
    deleted_count = 0
    for dir_name, dir_path in dirs_to_clean:
        if dir_path.exists():
            for file_path in dir_path.glob("*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        console.print(f"❌ Error deleting {file_path}: {e}")

    console.print(f"✅ [bold green]Cleaned {deleted_count} files[/bold green]")


@load_app.command("backup")
def backup_data(
    backup_dir: Optional[str] = typer.Option(None, help="Backup directory path"),
    include_raw: bool = typer.Option(True, help="Include raw JSON files in backup"),
) -> None:
    """Create a backup of pipeline data."""

    if backup_dir is None:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"Data/backups/pipeline_backup_{timestamp}"

    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    console.print(f"💾 [bold blue]Creating backup in {backup_path}[/bold blue]")

    processed_dir = Path("Data/cli_pipeline_data/processed_parquet")
    raw_dir = Path("Data/cli_pipeline_data/raw_json")

    import shutil

    backed_up_files = 0

    # Backup processed data
    if processed_dir.exists():
        backup_processed = backup_path / "processed_parquet"
        backup_processed.mkdir(exist_ok=True)

        for file_path in processed_dir.glob("*.parquet"):
            dest_path = backup_processed / file_path.name
            shutil.copy2(file_path, dest_path)
            backed_up_files += 1
            console.print(f"📄 Backed up {file_path.name}")

    # Backup raw data if requested
    if include_raw and raw_dir.exists():
        backup_raw = backup_path / "raw_json"
        backup_raw.mkdir(exist_ok=True)

        for file_path in raw_dir.glob("*.json"):
            dest_path = backup_raw / file_path.name
            shutil.copy2(file_path, dest_path)
            backed_up_files += 1
            console.print(f"📄 Backed up {file_path.name}")

    console.print(
        f"✅ [bold green]Backup complete![/bold green] {backed_up_files} files backed up to {backup_path}"
    )


@load_app.command("restore")
def restore_data(
    backup_dir: str = typer.Argument(..., help="Backup directory to restore from"),
    confirm: bool = typer.Option(False, help="Skip confirmation prompt"),
) -> None:
    """Restore pipeline data from a backup."""

    backup_path = Path(backup_dir)

    if not backup_path.exists():
        console.print(f"❌ Backup directory not found: {backup_path}")
        raise typer.Exit(code=1)

    console.print(f"🔄 [bold blue]Restoring from backup: {backup_path}[/bold blue]")

    # Check what's in the backup
    backup_processed = backup_path / "processed_parquet"
    backup_raw = backup_path / "raw_json"

    processed_files = (
        list(backup_processed.glob("*.parquet")) if backup_processed.exists() else []
    )
    raw_files = list(backup_raw.glob("*.json")) if backup_raw.exists() else []

    console.print("📊 Backup contains:")
    console.print(f"  • {len(processed_files)} processed files")
    console.print(f"  • {len(raw_files)} raw files")

    if not processed_files and not raw_files:
        console.print("❌ Backup appears to be empty")
        raise typer.Exit(code=1)

    # Confirm restore
    if not confirm:
        confirmed = typer.confirm(
            "This will overwrite existing pipeline data. Continue?"
        )
        if not confirmed:
            console.print("❌ Restore cancelled")
            return

    # Perform restore
    import shutil

    processed_dir = Path("Data/cli_pipeline_data/processed_parquet")
    raw_dir = Path("Data/cli_pipeline_data/raw_json")

    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    restored_count = 0

    # Restore processed files
    for file_path in processed_files:
        dest_path = processed_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        restored_count += 1
        console.print(f"📄 Restored {file_path.name}")

    # Restore raw files
    for file_path in raw_files:
        dest_path = raw_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        restored_count += 1
        console.print(f"📄 Restored {file_path.name}")

    console.print(
        f"✅ [bold green]Restore complete![/bold green] {restored_count} files restored"
    )


@load_app.command("export")
def export_data(
    table_name: str = typer.Argument(..., help="Table name to export"),
    output_path: Optional[str] = typer.Option(None, help="Output file path"),
    output_format: str = typer.Option("csv", help="Export format: csv or json"),
) -> None:
    """Export a pipeline table to CSV or JSON."""

    processed_dir = Path("Data/cli_pipeline_data/processed_parquet")
    input_path = processed_dir / f"{table_name}.parquet"

    if not input_path.exists():
        console.print(f"❌ Table not found: {input_path}")
        available_tables = [f.stem for f in processed_dir.glob("*.parquet")]
        if available_tables:
            console.print(f"Available tables: {', '.join(available_tables)}")
        raise typer.Exit(code=1)

    if output_path is None:
        output_path = f"{table_name}.{output_format}"

    output_file = Path(output_path)

    console.print(f"📤 [bold blue]Exporting {table_name} to {output_file}[/bold blue]")

    try:
        import polars as pl

        df = pl.read_parquet(input_path)

        if output_format.lower() == "csv":
            df.write_csv(output_file)
        elif output_format.lower() == "json":
            df.write_json(output_file)
        else:
            console.print(f"❌ Unsupported format: {output_format}")
            raise typer.Exit(code=1)

        file_size = output_file.stat().st_size
        size_mb = file_size / (1024 * 1024)

        console.print("✅ [bold green]Export complete![/bold green]")
        console.print(f"📊 Exported {len(df)} rows to {output_file} ({size_mb:.1f}MB)")

    except Exception as e:
        console.print(f"❌ Export failed: {e}")
        raise typer.Exit(code=1)
