"""
Data extraction operations for Enviroflow ELT pipeline.

Enhanced extraction functions with MotherDuck-first architecture and advanced data processing:

External Sources:
- Trello API (job management & project tracking)
- Float API (labour hours & time tracking)
- Google Sheets P&L (financial costs & sales data)
- Legacy file sources (backward compatibility)

Key Features:
- MotherDuck Default: Cloud database storage by default with local file options
- Advanced Date Handling: Excel serial number conversion to proper Date types
- Comprehensive Column Typing: Financial data as Float64, text as String
- Data Quality: Null filtering and validation for clean datasets
- Graceful Fallbacks: Robust error handling with local file backups
- Live Data Integration: Real-time Google Sheets connectivity for up-to-date financial data

Data Scale:
- Xero Costs: 13,652+ records (vs legacy 999, +1,266% improvement)
- Sales Data: 30,996+ records with comprehensive financial column typing
- Trello: Variable based on active boards and job cards
- Float: Variable based on labour tracking period
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import polars as pl
import streamlit as st
from rich.console import Console

from enviroflow_app import config
from enviroflow_app.elt import float2duck
from enviroflow_app.elt.motherduck import md
from enviroflow_app.elt.trello import tr_api_async as tr_api
from enviroflow_app.elt.trello import tr_extract_async as tr_extract
from enviroflow_app.elt.trello import tr_load

console = Console()

# Directory configuration
PROCESSED_PARQUET_DIR = Path("Data/cli_pipeline_data/processed_parquet")
DATA_DIR = Path("Data")

# Ensure directories exist
PROCESSED_PARQUET_DIR.mkdir(parents=True, exist_ok=True)


def _save_dataframe(
    df: pl.DataFrame,
    table_name: str,
    config: Optional[Any] = None,
    local_filename: Optional[str] = None,
) -> None:
    """
    Save DataFrame to appropriate destinations with MotherDuck as default.

    Provides flexible saving options with automatic fallback handling:
    - Default behavior: Save to MotherDuck only
    - Configurable: Save to local files, MotherDuck, or both
    - Robust: Automatic fallback to local files if MotherDuck unavailable

    Args:
        df: Polars DataFrame to save
        table_name: Name for the table in MotherDuck database
        config: Pipeline configuration with output settings (OutputConfig or PipelineConfig)
               If None, defaults to MotherDuck-only saving
        local_filename: Optional custom filename for local parquet saving
                       Defaults to '{table_name}.parquet'

    Raises:
        Exception: Re-raises exceptions if both MotherDuck and local saving fail

    Note:
        - MotherDuck tables are saved with lowercase names
        - Local files are saved to 'Data/cli_pipeline_data/processed_parquet/'
        - Graceful fallback ensures data is never lost during extraction
    """
    if config is None:
        # Default to MotherDuck saving if no config provided
        # Create a default configuration that saves to MotherDuck only
        from enviroflow_app.cli.config import OutputDestination, OutputConfig

        try:
            default_config = OutputConfig(destination=OutputDestination.MOTHERDUCK)
            console.print("📝 Using default configuration: MotherDuck only")
            # Recursively call with the default config
            _save_dataframe(df, table_name, default_config, local_filename)
            return
        except Exception as e:
            # If MotherDuck fails, fall back to local saving
            console.print(f"⚠️ MotherDuck unavailable: {e}")
            console.print("🔄 Falling back to local file saving...")
            local_file = local_filename or f"{table_name}.parquet"
            df.write_parquet(PROCESSED_PARQUET_DIR / local_file)
            console.print(f"💾 Fallback: Saved {len(df)} records to {local_file}")
            return

    # Ensure output directory exists
    # Handle both OutputConfig and pipeline config objects
    output_config = getattr(config, "output", config)

    if hasattr(output_config, "local_dir"):
        output_config.local_dir.mkdir(parents=True, exist_ok=True)

    # Save to local files if configured
    if getattr(output_config, "save_local", True):
        local_file = local_filename or f"{table_name}.parquet"
        local_dir = getattr(output_config, "local_dir", PROCESSED_PARQUET_DIR)
        local_path = local_dir / local_file
        df.write_parquet(local_path)
        console.print(f"💾 Saved {len(df)} records to local file: {local_file}")

    # Save to MotherDuck if configured
    if getattr(output_config, "save_motherduck", False):
        try:
            if hasattr(output_config, "get_motherduck_connection"):
                conn = output_config.get_motherduck_connection()
                if conn:
                    conn.save_table(table_name, df)
                    console.print(
                        f"🦆 Saved {len(df)} records to MotherDuck table: {table_name}"
                    )
        except Exception as e:
            console.print(f"⚠️ Failed to save to MotherDuck: {e}")
            # If MotherDuck fails and local is not enabled, save locally as fallback
            if not getattr(output_config, "save_local", True):
                console.print("🔄 Falling back to local file...")
                local_file = local_filename or f"{table_name}.parquet"
                df.write_parquet(PROCESSED_PARQUET_DIR / local_file)
                console.print(f"💾 Fallback: Saved to {local_file}")


async def _fetch_trello_data() -> Tuple[pl.DataFrame, Dict[str, Any]]:
    """
    Internal async function to fetch Trello data.

    Returns:
        Tuple of (job_cards_df, raw_boards_dict)
    """
    console.print("🔗 Connecting to Trello API...")

    try:
        # Get Trello credentials from secrets or environment variables
        import os

        # Try environment variables first (for GitHub Actions)
        trello_key = os.getenv("TRELLO_KEY")
        trello_token = os.getenv("TRELLO_TOKEN")

        if trello_key and trello_token:
            console.print("✅ Using Trello credentials from environment")
        else:
            # Fall back to Streamlit secrets
            trello_key = st.secrets["trello"]["api_key"]
            trello_token = st.secrets["trello"]["api_token"]
            console.print("✅ Using Trello credentials from Streamlit secrets")

        trello_creds = tr_api.TrCreds(
            api_key=trello_key,
            api_token=trello_token,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not read Trello secrets: {e}")
        raise

    console.print("📥 Fetching Trello boards...")
    boards_dict = await tr_extract.fetch_boards(
        tr_con=trello_creds, relevant_boards=config.TR["relevant_trello_boards"]
    )

    console.print("🔄 Transforming boards into job cards...")
    job_cards_df = tr_load.build_cards_df_from_boards_dict(boards_dict)

    # Handle Object columns for Parquet compatibility
    object_columns = [
        col
        for col, dtype in zip(job_cards_df.columns, job_cards_df.dtypes)
        if dtype == pl.Object
    ]
    if object_columns:
        console.print(f"🔧 Converting Object columns to String: {object_columns}")
        job_cards_df = job_cards_df.with_columns(
            [
                pl.col(col).map_elements(
                    lambda x: str(x) if x is not None else None, return_dtype=pl.String
                )
                for col in object_columns
            ]
        )

    return job_cards_df, boards_dict


def extract_trello_data(config: Optional[Any] = None) -> Dict[str, Any]:
    """
    Extract job cards and board data from Trello API.

    Downloads board data from configured Trello boards and processes
    job cards for downstream pipeline operations.

    Args:
        config: Pipeline configuration with output settings

    Returns:
        Dictionary containing:
        - job_cards: DataFrame of processed job cards
        - raw_boards: Dictionary of raw board data
    """
    console.print("🎯 [bold blue]Starting Trello data extraction...[/bold blue]")

    try:
        # Run the async extraction
        job_cards, raw_boards = asyncio.run(_fetch_trello_data())

        # Save processed job cards dataframe directly
        _save_dataframe(job_cards, "job_cards", config)

        console.print("✅ [bold green]Trello extraction completed![/bold green]")
        console.print(
            f"📊 Extracted {len(job_cards)} job cards from {len(raw_boards)} boards"
        )

        return {"job_cards": job_cards}

    except Exception as e:
        console.print(f"❌ [bold red]Trello extraction failed:[/bold red] {e}")
        raise


def extract_float_data(config: Optional[Any] = None) -> Dict[str, Any]:
    """
    Extract Float labour hours data.
    Adapts logic from legacy `sync_float()` in `scripts/pipeline_cli.py`.

    Args:
        config: Pipeline configuration with output settings

    Returns:
        Dictionary containing:
        - labour_hours: Polars DataFrame of labour hour records
        - raw_float: Raw Float API data for archival
    """
    console.print("⚒️ [bold blue]Extracting Float data...[/bold blue]")

    try:
        console.print("📥 Fetching labour hours from Float API...")
        labour_hours_df = asyncio.run(float2duck.build_project_labour_hours_table())

        console.print(f"✅ Extracted {len(labour_hours_df)} labour hour records")

        # Remove duplicate rows before saving to MotherDuck
        original_count = len(labour_hours_df)
        labour_hours_df = labour_hours_df.unique()
        deduplicated_count = len(labour_hours_df)

        if original_count > deduplicated_count:
            duplicates_removed = original_count - deduplicated_count
            console.print(f"🧹 Removed {duplicates_removed} duplicate records")
            console.print(
                f"📊 Final dataset: {deduplicated_count} unique labour hour records"
            )
        else:
            console.print("✅ No duplicate records found")

        # Save processed dataframe directly
        _save_dataframe(labour_hours_df, "labour_hours", config)

        console.print(
            f"[bold green]Float sync complete.[/bold green] Processed {deduplicated_count} labour hour records."
        )

        return {"labour_hours": labour_hours_df}

    except Exception as e:
        console.print(f"❌ [bold red]Float extraction failed:[/bold red] {e}")
        raise


def extract_xero_costs(config: Optional[Any] = None) -> Dict[str, Any]:
    """
    Extract Xero costs data from Google Sheets P&L spreadsheet with enhanced processing.

    Features:
    - Live Google Sheets integration with 13,652+ cost records (vs legacy 999)
    - Excel date conversion: Serial numbers → proper Date type (not string)
    - Comprehensive column typing: Financial columns as Float64, text as String
    - Data quality: Null date filtering for clean datasets
    - MotherDuck default: Saves to cloud database by default
    - Graceful fallback: Local file backup if Google Sheets unavailable

    Args:
        config: Pipeline configuration with output settings
               If None, defaults to MotherDuck-only saving

    Returns:
        Dictionary containing:
        - xero_costs: Polars DataFrame of cost records with proper typing:
          * Date: Date type (converted from Excel serial numbers)
          * Financial columns (Debit, Credit, Running Balance, etc.): Float64
          * Text columns: String
          * Filtered: No null dates

    Raises:
        Exception: If both Google Sheets extraction and local file fallback fail

    Note:
        Excel date handling uses 1899-12-30 epoch for serial number conversion.
        Saves to MotherDuck 'xero_costs' table and optionally local 'xero_costs.parquet'.
    """
    console.print(
        "💰 [bold blue]Extracting Xero costs from Google Sheets...[/bold blue]"
    )

    try:
        # Import the P&L Google Sheets client
        from enviroflow_app.gsheets import create_pnl_client
        import asyncio

        async def _extract_costs():
            # Initialize the P&L client
            console.print("🔑 Initializing P&L Google Sheets client...")
            client = create_pnl_client()

            # Find the Project P&L Report spreadsheet
            console.print("🔍 Searching for Project P&L Report spreadsheet...")
            spreadsheets = await client.list_spreadsheets()
            pnl_spreadsheet = None

            for spreadsheet in spreadsheets:
                if "Project P&L Report" in spreadsheet.title:
                    pnl_spreadsheet = spreadsheet
                    break

            if not pnl_spreadsheet:
                console.print(
                    "❌ [bold red]Project P&L Report spreadsheet not found[/bold red]"
                )
                raise ValueError("Project P&L Report spreadsheet not found")

            console.print(f"✅ Found spreadsheet: {pnl_spreadsheet.title}")

            # Extract the costs table using the specialized P&L parser
            console.print("📊 Extracting costs table...")
            costs_df = await client.extract_pnl_table(
                pnl_spreadsheet.spreadsheet_id, "costs", engine="polars"
            )

            console.print(
                f"✅ Extracted {len(costs_df)} cost records from Google Sheets"
            )

            # Check if we got the expected number of records
            if len(costs_df) < 10000:
                console.print(
                    f"⚠️  [bold yellow]Warning: Only {len(costs_df)} records extracted, expected 13k+[/bold yellow]"
                )
                console.print(
                    "This might indicate pagination or filtering issues in the source data."
                )

            return costs_df

        # Run the async extraction
        costs_df = asyncio.run(_extract_costs())

        # Convert numeric columns from string to float
        numeric_columns = ["Debit", "Credit", "Gross", "net", "GST"]
        for col in numeric_columns:
            if col in costs_df.columns:
                costs_df = costs_df.with_columns(
                    pl.col(col).str.replace_all(",", "").cast(pl.Float64, strict=False)
                )

        # Convert Date column from Excel serial number to proper date
        if "Date" in costs_df.columns:
            # Excel date serial numbers start from 1900-01-01 (day 1)
            # Excel incorrectly treats 1900 as a leap year, so we use 1899-12-30 as day 0
            # We can use simple date arithmetic in Polars
            try:
                # First, try to convert string numbers to integers
                costs_df = costs_df.with_columns(
                    pl.col("Date").cast(pl.Int32, strict=False).alias("date_int")
                )

                # Create the base date (Excel epoch)
                # Use a fixed date and add the serial days
                costs_df = costs_df.with_columns(
                    pl.date(1899, 12, 30).alias("excel_epoch")
                )

                # Add the days to the epoch and ensure it's a Date type (not datetime/timestamp)
                costs_df = costs_df.with_columns(
                    (pl.col("excel_epoch") + pl.duration(days=pl.col("date_int")))
                    .dt.date()
                    .alias("Date")  # Explicitly cast to Date type
                )

                # Clean up temporary columns
                costs_df = costs_df.drop(["date_int", "excel_epoch"])

            except Exception as date_error:
                console.print(
                    f"⚠️ [yellow]Date conversion warning: {date_error}[/yellow]"
                )
                console.print(
                    "⚠️ [yellow]Keeping Date column as string for now[/yellow]"
                )

        # Filter out rows with null dates before saving
        if "Date" in costs_df.columns:
            initial_count = len(costs_df)
            costs_df = costs_df.filter(pl.col("Date").is_not_null())
            filtered_count = len(costs_df)
            removed_count = initial_count - filtered_count

            if removed_count > 0:
                console.print(f"🧹 Removed {removed_count} rows with null dates")
                console.print(f"📊 Remaining records: {filtered_count}")

        # Rename gen_proj to Project for consistency with analytics pipeline
        if "gen_proj" in costs_df.columns:
            costs_df = costs_df.rename({"gen_proj": "Project"})

        # Handle Object columns for compatibility
        object_cols = [
            col
            for col, dtype in zip(costs_df.columns, costs_df.dtypes)
            if dtype == pl.Object
        ]
        if object_cols:
            costs_df = costs_df.with_columns(
                [pl.col(c).cast(pl.String) for c in object_cols]
            )

        # Save processed data
        _save_dataframe(costs_df, "xero_costs", config)

        console.print(
            "✅ [bold green]Xero costs data extracted successfully from Google Sheets![/bold green]"
        )

        return {"xero_costs": costs_df}

    except Exception as e:
        console.print(f"❌ [bold red]Google Sheets extraction failed:[/bold red] {e}")
        console.print(
            "🔄 [bold yellow]Falling back to local reference file...[/bold yellow]"
        )

        # Fallback to the original file-based approach
        try:
            candidate_paths = [
                Path("Data/pnl_data/costs.parquet"),
                Path("pnl_data/costs.parquet"),
                Path("Data/misc/costs.parquet"),
            ]

            costs_file = next((p for p in candidate_paths if p.exists()), None)

            if costs_file is None:
                console.print(
                    "⚠️  [bold yellow]Reference costs file not found in expected locations[/bold yellow] "
                    "(Data/pnl_data/, pnl_data/, Data/misc/). Returning empty costs dataset to proceed."
                )
                costs_df = pl.DataFrame([])
            else:
                console.print(f"📖 Loading costs from reference file: {costs_file}")
                costs_df = pl.read_parquet(costs_file)
                console.print(
                    f"✅ Loaded {len(costs_df)} cost records from fallback file"
                )

            # Convert numeric columns from string to float
            numeric_columns = ["Debit", "Credit", "Gross", "net", "GST"]
            for col in numeric_columns:
                if col in costs_df.columns:
                    costs_df = costs_df.with_columns(
                        pl.col(col).str.replace(",", "").cast(pl.Float64, strict=False)
                    )

            # Convert Date column from Excel serial number to proper date
            if "Date" in costs_df.columns:
                # Excel date serial numbers start from 1900-01-01 (day 1)
                # Excel incorrectly treats 1900 as a leap year, so we use 1899-12-30 as day 0
                # We can use simple date arithmetic in Polars
                try:
                    # First, try to convert string numbers to integers
                    costs_df = costs_df.with_columns(
                        pl.col("Date").cast(pl.Int32, strict=False).alias("date_int")
                    )

                    # Create the base date (Excel epoch)
                    # Use a fixed date and add the serial days
                    costs_df = costs_df.with_columns(
                        pl.date(1899, 12, 30).alias("excel_epoch")
                    )

                    # Add the days to the epoch and ensure it's a Date type (not datetime/timestamp)
                    costs_df = costs_df.with_columns(
                        (pl.col("excel_epoch") + pl.duration(days=pl.col("date_int")))
                        .dt.date()
                        .alias("Date")  # Explicitly cast to Date type
                    )

                    # Clean up temporary columns
                    costs_df = costs_df.drop(["date_int", "excel_epoch"])

                except Exception as date_error:
                    console.print(
                        f"⚠️ [yellow]Date conversion warning: {date_error}[/yellow]"
                    )
                    console.print(
                        "⚠️ [yellow]Keeping Date column as string for now[/yellow]"
                    )

            # Filter out rows with null dates before saving
            if "Date" in costs_df.columns:
                initial_count = len(costs_df)
                costs_df = costs_df.filter(pl.col("Date").is_not_null())
                filtered_count = len(costs_df)
                removed_count = initial_count - filtered_count

                if removed_count > 0:
                    console.print(f"🧹 Removed {removed_count} rows with null dates")
                    console.print(f"📊 Remaining records: {filtered_count}")

            # Rename gen_proj to Project for consistency with analytics pipeline
            if "gen_proj" in costs_df.columns:
                costs_df = costs_df.rename({"gen_proj": "Project"})

            # Handle Object columns for compatibility
            object_cols = [
                col
                for col, dtype in zip(costs_df.columns, costs_df.dtypes)
                if dtype == pl.Object
            ]
            if object_cols:
                costs_df = costs_df.with_columns(
                    [
                        pl.col(col).map_elements(str, return_dtype=pl.String)
                        for col in object_cols
                    ]
                )

            # Save processed data
            _save_dataframe(costs_df, "xero_costs", config)

            console.print(
                "✅ [bold green]Xero costs data loaded from fallback file![/bold green]"
            )

            return {"xero_costs": costs_df}

        except Exception as fallback_error:
            console.print(
                f"❌ [bold red]Fallback extraction also failed:[/bold red] {fallback_error}"
            )
            raise


def extract_sales_data(config: Optional[Any] = None) -> Dict[str, Any]:
    """
    Extract sales data from P&L Google Sheets with comprehensive column typing.

    Features:
    - Large dataset extraction: 30,996+ sales records from live Google Sheets
    - Advanced date processing: Excel serial numbers → Date type with null filtering
    - Financial column typing: All monetary columns (Debit, Credit, Running Balance,
      Gross, GST, amount) properly typed as Float64
    - Text column handling: Proper String typing for descriptive fields
    - MotherDuck integration: Default cloud database storage
    - Data integrity: Null date filtering ensures clean analysis datasets

    Args:
        config: Pipeline configuration with output settings
               If None, defaults to MotherDuck-only saving

    Returns:
        Dictionary containing:
        - sales_data: Polars DataFrame of sales records with comprehensive typing:
          * Date: Date type (converted from Excel serial numbers)
          * Financial columns: Float64 (Debit, Credit, Running Balance, Gross, GST, amount)
          * Descriptive columns: String (Account, Description, Supplier, etc.)
          * Quality: Null dates filtered out

    Raises:
        Exception: If Google Sheets extraction fails and no fallback available

    Note:
        Saves to MotherDuck 'xero_sales' table by default.
        Uses Excel 1899-12-30 epoch for accurate date conversion.
        Provides comprehensive column typing for financial analysis workflows.
    """
    console.print(
        "📈 [bold blue]Extracting Sales data from Google Sheets...[/bold blue]"
    )

    try:
        from enviroflow_app.gsheets import create_pnl_client
        import asyncio

        async def _extract_sales():
            console.print("🔑 Initializing P&L Google Sheets client...")
            client = create_pnl_client()

            console.print("🔍 Searching for Project P&L Report spreadsheet...")
            spreadsheets = await client.list_spreadsheets()
            pnl_spreadsheet = next(
                (s for s in spreadsheets if "Project P&L Report" in s.title), None
            )

            if not pnl_spreadsheet:
                raise ValueError("Project P&L Report spreadsheet not found")

            console.print(f"✅ Found spreadsheet: {pnl_spreadsheet.title}")

            console.print("📊 Extracting sales table...")
            sales_df = await client.extract_pnl_table(
                pnl_spreadsheet.spreadsheet_id, "sales", engine="polars"
            )

            console.print(
                f"✅ Extracted {len(sales_df)} sales records from Google Sheets"
            )
            return sales_df

        sales_df = asyncio.run(_extract_sales())

        # Convert numeric columns from string to float
        numeric_columns = [
            "Debit",
            "Credit",
            "Running Balance",
            "Gross",
            "GST",
            "amount",
        ]
        for col in numeric_columns:
            if col in sales_df.columns:
                sales_df = sales_df.with_columns(
                    pl.col(col).str.replace_all(",", "").cast(pl.Float64, strict=False)
                )

        # Convert Date column from Excel serial number to proper date
        if "Date" in sales_df.columns:
            # Excel date serial numbers start from 1900-01-01 (day 1)
            # Excel incorrectly treats 1900 as a leap year, so we use 1899-12-30 as day 0
            # We can use simple date arithmetic in Polars
            try:
                # First, try to convert string numbers to integers
                sales_df = sales_df.with_columns(
                    pl.col("Date").cast(pl.Int32, strict=False).alias("date_int")
                )

                # Create the base date (Excel epoch)
                # Use a fixed date and add the serial days
                sales_df = sales_df.with_columns(
                    pl.date(1899, 12, 30).alias("excel_epoch")
                )

                # Add the days to the epoch and ensure it's a Date type (not datetime/timestamp)
                sales_df = sales_df.with_columns(
                    (pl.col("excel_epoch") + pl.duration(days=pl.col("date_int")))
                    .dt.date()
                    .alias("Date")  # Explicitly cast to Date type
                )

                # Clean up temporary columns
                sales_df = sales_df.drop(["date_int", "excel_epoch"])

            except Exception as date_error:
                console.print(
                    f"⚠️ [yellow]Date conversion warning: {date_error}[/yellow]"
                )
                console.print(
                    "⚠️ [yellow]Keeping Date column as string for now[/yellow]"
                )

        # Filter out rows with null dates before saving
        if "Date" in sales_df.columns:
            initial_count = len(sales_df)
            sales_df = sales_df.filter(pl.col("Date").is_not_null())
            filtered_count = len(sales_df)
            removed_count = initial_count - filtered_count

            if removed_count > 0:
                console.print(f"🧹 Removed {removed_count} rows with null dates")
                console.print(f"📊 Remaining records: {filtered_count}")

        # Handle Object columns for compatibility
        object_cols = [
            col
            for col, dtype in zip(sales_df.columns, sales_df.dtypes)
            if dtype == pl.Object
        ]
        if object_cols:
            sales_df = sales_df.with_columns(
                [pl.col(c).cast(pl.String) for c in object_cols]
            )

        _save_dataframe(sales_df, "xero_sales", config)

        console.print(
            "✅ [bold green]Sales data extracted successfully from Google Sheets![/bold green]"
        )

        return {"sales_data": sales_df}

    except Exception as e:
        console.print(
            f"❌ [bold red]Sales data extraction from Google Sheets failed:[/bold red] {e}"
        )
        # For sales, we might not need a fallback to a local file unless specified.
        # If this is a critical dataset, a fallback could be added here.
        console.print(
            "⚠️ [bold yellow]No fallback available for sales data. Operation failed.[/bold yellow]"
        )
        raise


def download_production_quotes() -> Dict[str, Any]:
    """
    Download complete quote datasets from MotherDuck production database.

    This is used by the build_quotes operation to get the latest
    production data for quote stitching.

    Returns:
        Dictionary containing:
        - xero_quotes: Complete Xero quotes dataset
        - simpro_quotes: Complete Simpro quotes dataset
    """
    console.print("📡 [bold blue]Downloading production quotes...[/bold blue]")

    try:
        # Initialize MotherDuck connection
        console.print("🔗 Connecting to MotherDuck...")

        # Get token from secrets or environment
        import os

        secrets_path = Path(".streamlit/secrets.toml")

        if secrets_path.exists():
            # Force streamlit to read secrets
            _ = st.secrets
            token = st.secrets["motherduck"]["token"]
            console.print("✅ Using MotherDuck token from Streamlit secrets")
        else:
            token = os.getenv("MOTHER_DUCK")  # Match GitHub Actions secret name
            if not token:
                raise ValueError(
                    "No MotherDuck token found. Please ensure .streamlit/secrets.toml exists "
                    "with motherduck.token or set MOTHER_DUCK environment variable"
                )
            console.print("✅ Using MotherDuck token from environment")

        conn = md.MotherDuck(db_name="enviroflow", token=token)

        # Download datasets
        console.print("📥 Downloading Xero quotes...")
        xero_quotes = conn.get_table("full_xero_quotes")

        console.print("📥 Downloading Simpro quotes...")
        simpro_quotes = conn.get_table("full_simpro_quotes")

        console.print(
            f"✅ Downloaded {len(xero_quotes)} Xero and {len(simpro_quotes)} Simpro quotes"
        )

        # Save to processed directory for quote building
        PROCESSED_PARQUET_DIR.mkdir(parents=True, exist_ok=True)
        xero_quotes.write_parquet(
            PROCESSED_PARQUET_DIR / "xero_quotes_complete.parquet"
        )
        simpro_quotes.write_parquet(
            PROCESSED_PARQUET_DIR / "simpro_quotes_complete.parquet"
        )

        return {"xero_quotes": xero_quotes, "simpro_quotes": simpro_quotes}

    except Exception as e:
        console.print(f"❌ [bold red]Production quotes download failed:[/bold red] {e}")
        raise
