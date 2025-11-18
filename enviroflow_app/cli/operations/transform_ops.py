"""
Data transformation operations for Enviroflow ELT pipeline.

Contains functions for transforming raw data into business objects:
- Quote stitching and normalization
- Job card processing and customer extraction
- Labour hour integration
- Project aggregation and analytics
"""

from pathlib import Path
from typing import Any, Dict, Optional

import polars as pl
from rich.console import Console

console = Console()

# Directory configuration
PROCESSED_PARQUET_DIR = Path("Data/cli_pipeline_data/processed_parquet")


def _save_dataframe(
    df: pl.DataFrame,
    table_name: str,
    config: Optional[Any] = None,
    local_filename: Optional[str] = None,
) -> None:
    """
    Save DataFrame to appropriate destination(s) based on configuration.

    Args:
        df: DataFrame to save
        table_name: Name for the table in MotherDuck
        config: Pipeline configuration with output settings
        local_filename: Optional custom filename for local saving
    """
    if config is None:
        # If no config, do not save locally or to MotherDuck
        console.print(f"⚠️ No config provided for saving {table_name}. Skipping save.")
        return

    # Ensure output directory exists if saving locally
    if config.output.save_local:
        config.output.ensure_local_dir()
        local_file = local_filename or f"{table_name}.parquet"
        local_path = config.output.local_dir / local_file
        df.write_parquet(local_path)
        console.print(f"💾 Saved {len(df)} records to local file: {local_file}")

    # Save to MotherDuck if configured
    if config.output.save_motherduck:
        try:
            conn = config.output.get_motherduck_connection()
            if conn:
                conn.save_table(table_name, df)
                console.print(
                    f"🦆 Saved {len(df)} records to MotherDuck table: {table_name}"
                )
        except Exception as e:
            console.print(f"⚠️ Failed to save to MotherDuck: {e}")


def build_quotes_table(
    xero_quotes: Optional[pl.DataFrame] = None,
    simpro_quotes: Optional[pl.DataFrame] = None,
    config: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Build unified quotes table from Xero and Simpro sources.
    Adapts logic from legacy `build_quotes()` and `stitch_quotes_from_test_data()`
    in `scripts/pipeline_cli.py`.

    Args:
        xero_quotes: Xero quotes DataFrame from DAG.
        simpro_quotes: Simpro quotes DataFrame from DAG.
        config: Pipeline configuration with output settings

    Returns:
        Dictionary containing:
        - quotes: Unified quotes DataFrame
    """
    console.print("🔗 [bold blue]Building unified quotes table...[/bold blue]")

    try:
        # In the new CLI, we expect data to be passed from the DAG.
        # The loading from file logic is a fallback for standalone execution.
        if xero_quotes is None:
            from .extraction_ops import download_production_quotes

            console.print(
                "📥 xero_quotes not provided via DAG, downloading production quotes..."
            )
            production_data = download_production_quotes()
            xero_quotes = production_data["xero_quotes"]
            simpro_quotes = production_data["simpro_quotes"]

        if simpro_quotes is None:
            # This case should ideally not be hit if the above logic is sound
            simpro_path = PROCESSED_PARQUET_DIR / "simpro_quotes_complete.parquet"
            if not simpro_path.exists():
                raise FileNotFoundError(
                    "simpro_quotes not provided and file not found."
                )
            console.print(f"📖 Loading Simpro quotes from {simpro_path}")
            simpro_quotes = pl.read_parquet(simpro_path)

        if xero_quotes is None or simpro_quotes is None:
            raise ValueError("Could not load quotes data.")

        console.print(
            f"📊 Input: {len(simpro_quotes)} Simpro quotes, {len(xero_quotes)} Xero quotes"
        )

        # This normalization logic is adapted from the legacy `stitch_quotes_from_test_data`
        console.print("🔧 Normalizing Xero quotes...")
        xero_cols_to_drop = [
            col
            for col in [
                "__index_level_0__",
                "updated",
                "quote_id",
                "line_id",
                "contact_id",
            ]
            if col in xero_quotes.columns
        ]
        normalized_xero = xero_quotes.drop(xero_cols_to_drop).select(
            pl.col("quote_no"),
            pl.col("quote_ref"),
            pl.col("customer"),
            pl.col("quote_status"),
            pl.col("item_desc"),
            pl.col("item_code"),
            pl.col("line_pct"),
            pl.col("quantity"),
            pl.col("unit_price"),
            pl.col("line_total"),
            pl.col("created").cast(pl.Date),
            pl.lit("Xero").alias("quote_source"),
        )

        console.print("🔧 Normalizing Simpro quotes...")
        if "quote_source" not in simpro_quotes.columns:
            simpro_quotes = simpro_quotes.with_columns(
                pl.lit("Simpro").alias("quote_source")
            )

        simpro_cols_to_drop = [
            col
            for col in ["quote_total", "date_approved"]
            if col in simpro_quotes.columns
        ]
        normalized_simpro = (
            simpro_quotes.drop(simpro_cols_to_drop)
            .rename(
                {
                    "site": "quote_ref",
                    "date_created": "created",
                    "item": "item_desc",
                    "total": "line_total",
                }
            )
            .select(
                pl.col("quote_no"),
                pl.col("quote_ref"),
                pl.col("customer"),
                pl.lit("").alias("quote_status"),
                pl.col("item_desc"),
                pl.lit("").alias("item_code"),
                pl.col("line_pct"),
                pl.col("quantity"),
                pl.col("unit_price"),
                pl.col("line_total"),
                pl.col("created").cast(pl.Date),
                pl.col("quote_source"),
            )
        )

        console.print("🔗 Combining normalized datasets...")
        stitched_quotes = pl.concat([normalized_simpro, normalized_xero]).with_columns(
            pl.when(pl.col("line_pct") == 0)
            .then(1)
            .otherwise(pl.col("line_pct"))
            .alias("line_pct"),
        )

        # Save unified quotes table
        _save_dataframe(stitched_quotes, "quotes", config)

        console.print(
            f"✅ Created unified quotes table with {len(stitched_quotes)} records"
        )

        return {"quotes": stitched_quotes}

    except Exception as e:
        console.print(f"❌ [bold red]Quote building failed:[/bold red] {e}")
        raise


def build_jobs_table(
    job_cards: pl.DataFrame, quotes: pl.DataFrame, config: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Transforms raw job cards data into jobs table (Parquet).
    Generates the base 'jobs' table following the original ELT pipeline pattern.
    Adapts logic from legacy `build_jobs()` in `scripts/pipeline_cli.py`.

    Args:
        job_cards: Raw job cards DataFrame from Trello (from DAG)
        quotes: Unified quotes DataFrame (from DAG)
        config: Pipeline configuration with output settings

    Returns:
        Dictionary containing:
        - jobs: Jobs DataFrame
        - job_quote_mapping: Mapping between jobs and quotes
    """
    console.print("🏗️ [bold blue]Building jobs from job cards...[/bold blue]")
    try:
        console.print(
            f"📂 Loaded {len(job_cards)} job cards and {len(quotes)} quotes from DAG"
        )

        # Import transformation modules inside function to avoid circular imports
        from enviroflow_app.elt.transform import from_job_cards, from_quotes, from_jobs

        # Build quotes mapping
        console.print("🔗 Building jobs-to-quotes mapping...")
        from_quotes_processor = from_quotes.From_Quotes_Data(quotes_df=quotes)
        jobs2quotes_map = from_quotes_processor.jobs2quotes_map
        console.print(f"📊 Created mapping for {len(jobs2quotes_map)} jobs with quotes")

        # Build jobs dict using the original ELT pattern
        console.print("🏗️ Building jobs dictionary...")
        from_job_cards_processor = from_job_cards.From_Job_Cards(job_cards=job_cards)
        job_parse_results = from_job_cards_processor.build_jobs_dict(jobs2quotes_map)

        # Create job-to-quote mapping table for persistence and debugging
        console.print("🔗 Creating job-to-quote mapping table...")
        job_quote_mapping = []

        for job_name, job in job_parse_results.jobs.items():
            if job.quotes:
                for quote in job.quotes:
                    job_quote_mapping.append(
                        {
                            "job_name": job_name,
                            "job_no": job.id if hasattr(job, "id") else job_name,
                            "quote_no": quote.quote_no,
                            "quote_ref": quote.quote_ref,
                            "match_type": "primary",
                            "quote_value": quote.quote_value
                            if hasattr(quote, "quote_value")
                            else None,
                        }
                    )

            if job.variation_quotes:
                for quote in job.variation_quotes:
                    job_quote_mapping.append(
                        {
                            "job_name": job_name,
                            "job_no": job.id if hasattr(job, "id") else job_name,
                            "quote_no": quote.quote_no,
                            "quote_ref": quote.quote_ref,
                            "match_type": "variation",
                            "quote_value": quote.quote_value
                            if hasattr(quote, "quote_value")
                            else None,
                        }
                    )

        # Add jobs without quotes to mapping table
        for job_name, job in job_parse_results.no_quotes_matched.items():
            job_quote_mapping.append(
                {
                    "job_name": job_name,
                    "job_no": job.id if hasattr(job, "id") else job_name,
                    "quote_no": None,
                    "quote_ref": None,
                    "match_type": "no_match",
                    "quote_value": None,
                }
            )

        # Create DataFrame and save mapping table
        job_quote_mapping_df = (
            pl.DataFrame(job_quote_mapping) if job_quote_mapping else pl.DataFrame()
        )
        if not job_quote_mapping_df.is_empty():
            _save_dataframe(job_quote_mapping_df, "job_quote_mapping", config)
            console.print(
                f"📊 Job-quote mapping created with {len(job_quote_mapping_df)} records"
            )

        # Convert jobs dict to DataFrame using From_Jobs_Dict
        console.print("📋 Converting jobs to DataFrame...")
        jobs_df = from_jobs.From_Jobs_Dict(job_parse_results.jobs).jobs_df
        no_quotes_matched_df = from_jobs.From_Jobs_Dict(
            job_parse_results.no_quotes_matched
        ).jobs_df

        # Save the main jobs table
        _save_dataframe(jobs_df, "jobs", config)

        # Save debug tables
        debug_tables = []
        if len(job_parse_results.removed_cards) > 0:
            debug_tables.append(("removed_cards", job_parse_results.removed_cards))
        if len(no_quotes_matched_df) > 0:
            debug_tables.append(("job_no_quotes_matched", no_quotes_matched_df))
        if job_parse_results.attatched_card_not_parsed:
            debug_tables.append(
                (
                    "job_attached_cards_not_jobs",
                    pl.from_dicts(job_parse_results.attatched_card_not_parsed),
                )
            )

        for table_name, table_df in debug_tables:
            _save_dataframe(table_df, f"debug_{table_name}", config)

        console.print(f"✅ Jobs table created with {len(jobs_df)} records")
        console.print("📊 Summary:")
        console.print(f"  • Total jobs: {len(jobs_df)}")
        console.print(f"  • Jobs without quotes: {len(no_quotes_matched_df)}")
        console.print(f"  • Removed cards: {len(job_parse_results.removed_cards)}")

        return {"jobs": jobs_df, "job_quote_mapping": job_quote_mapping_df}

    except Exception as e:
        console.print(f"❌ [bold red]Jobs building failed:[/bold red] {e}")
        import traceback

        console.print(f"Full traceback: {traceback.format_exc()}")
        raise


def build_customers_table(
    job_cards: pl.DataFrame, config: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Extract unique customers from job cards.
    Adapts logic from legacy `build_customers()` in `scripts/pipeline_cli.py`.

    Args:
        job_cards: Raw job cards DataFrame from Trello (from DAG)

    Returns:
        Dictionary containing:
        - customers: Customers DataFrame
    """
    console.print("👥 [bold blue]Building customers table...[/bold blue]")

    # Import transformation module (function-level to avoid circular imports)
    from enviroflow_app.elt.transform.from_job_cards import From_Job_Cards

    console.print("🔄 Extracting unique customers from job cards...")
    customers_df = From_Job_Cards(job_cards).customers_df

    # Save customers table using _save_dataframe (MotherDuck/local)
    # config must be passed from caller
    _save_dataframe(customers_df, "customers", config)

    console.print(
        f"✅ Customers table built successfully. Generated {len(customers_df)} customer records."
    )

    return {"customers": customers_df}


def add_labour_to_jobs(
    jobs: pl.DataFrame,
    labour_hours: pl.DataFrame,
    quotes: pl.DataFrame,
    config: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Adds labour hours to jobs and create analytics tables.
    Adapts logic from legacy `add_labour()` in `scripts/pipeline_cli.py`.

    Args:
        jobs: Jobs DataFrame from DAG
        labour_hours: Labour hours DataFrame from DAG
        quotes: Unified quotes DataFrame from DAG

    Returns:
        Dictionary containing:
        - jobs_with_hours: Jobs with labour hours added
        - jobs_for_analytics: Enhanced jobs table for analytics
    """
    console.print("⚒️ [bold blue]Adding labour hours to jobs...[/bold blue]")

    console.print("📖 Processing labour records and building quotes dictionary...")

    # Import transformation modules (function-level to avoid circular imports)
    from enviroflow_app.elt.transform.from_labour_records import From_Labour_Records
    from enviroflow_app.elt.transform.from_quotes import From_Quotes_Data
    from enviroflow_app.elt.transform.from_jobs_with_labour import From_Jobs_With_Labour

    # Build quotes dictionary
    quotes_dict = From_Quotes_Data(quotes).quotes_dict

    # Add labour hours to jobs
    labour_processor = From_Labour_Records(labour_hours)
    jobs_with_labour_results = labour_processor.jobs_with_labour(jobs)

    console.print("📊 Building job analytics table...")
    job_analytics_processor = From_Jobs_With_Labour(
        jobs_with_labour_results.jobs_df, quotes_dict
    )
    job_analytics_df = job_analytics_processor.job_analytics_table

    # Save outputs using _save_dataframe (MotherDuck/local)
    # config must be passed from caller
    _save_dataframe(jobs_with_labour_results.jobs_df, "jobs_with_hours", config)
    _save_dataframe(job_analytics_df, "jobs_for_analytics", config)

    # Save debug tables
    debug_tables = [
        ("aggregated_labour_hours", jobs_with_labour_results.aggregated_df),
        ("removed_hours_records", jobs_with_labour_results.removed),
        ("job_no_hours_records", jobs_with_labour_results.job_no_hour_data),
    ]

    for debug_name, debug_df in debug_tables:
        if not debug_df.is_empty():
            _save_dataframe(debug_df, f"debug_{debug_name}", config)

    console.print("✅ [bold green]Labour hours added successfully![/bold green]")
    console.print("📊 Summary:")
    console.print(
        f"  • Jobs with labour: {len(jobs_with_labour_results.jobs_df)} records"
    )
    console.print(f"  • Job analytics: {len(job_analytics_df)} records")
    console.print(
        f"  • Excluded labour records: {len(jobs_with_labour_results.removed)}"
    )
    console.print(
        f"  • Jobs without hour data: {len(jobs_with_labour_results.job_no_hour_data)}"
    )

    return {
        "jobs_with_hours": jobs_with_labour_results.jobs_df,
        "jobs_for_analytics": job_analytics_df,
    }


def build_projects_table(
    jobs_with_hours: pl.DataFrame, quotes: pl.DataFrame, config: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Builds the final projects table from jobs with labour hours.
    Adapts logic from legacy `build_projects()` in `scripts/pipeline_cli.py`.

    Args:
        jobs_with_hours: Jobs DataFrame with labour hours (from DAG)
        quotes: Unified quotes DataFrame (from DAG)

    Returns:
        Dictionary containing:
        - projects: Projects DataFrame
    """
    console.print("🏗️ [bold blue]Building projects table...[/bold blue]")

    try:
        console.print("🔄 Building quotes dictionary and projects...")

        # Import transformation modules (function-level to avoid circular imports)
        from enviroflow_app.elt.transform.from_quotes import From_Quotes_Data
        from enviroflow_app.elt.transform.from_jobs_with_labour import (
            From_Jobs_With_Labour,
        )
        from enviroflow_app.elt.transform.from_projects_dict import (
            From_Raw_Projects_Dict,
        )

        # Build quotes dictionary
        quotes_dict = From_Quotes_Data(quotes).quotes_dict

        # Build projects from jobs with labour
        projects_processor = From_Jobs_With_Labour(jobs_with_hours, quotes_dict)
        projects_dict = projects_processor.projects

        console.print("📊 Converting projects dictionary to table...")
        projects_table_processor = From_Raw_Projects_Dict(projects_dict)
        projects_df = projects_table_processor.projects_table

        # Save projects table using _save_dataframe (MotherDuck/local)
        # config should be passed from caller
        _save_dataframe(projects_df, "projects", config)

        console.print("[bold green]Projects table built successfully.[/bold green]")
        console.print(f"  - Generated {len(projects_df)} project records")
        console.print(f"  - Processed {len(projects_dict)} project groups")

        return {"projects": projects_df}

    except Exception as e:
        console.print(f"❌ [bold red]Projects building failed:[/bold red] {e}")
        raise


def build_projects_analytics(
    projects: pl.DataFrame,
    jobs_analytics: pl.DataFrame,
    quotes: pl.DataFrame,
    labour_hours: pl.DataFrame,
    costs: pl.DataFrame,
    config: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Build projects_for_analytics table with enriched financial data.
    Adapts logic from legacy `build_projects_analytics()` in `scripts/pipeline_cli.py`.

    Args:
        projects: Basic projects DataFrame from DAG
        jobs_analytics: Jobs analytics DataFrame from DAG
        quotes: Unified quotes DataFrame from DAG
        labour_hours: Labour hours DataFrame from DAG
        costs: Xero costs DataFrame from DAG

    Returns:
        Dictionary containing:
        - projects_for_analytics: Enriched projects DataFrame
    """
    console.print("📊 [bold blue]Building projects_for_analytics table...[/bold blue]")

    try:
        console.print("🔄 Building enriched projects with financial data...")

        # Import transformation modules (function-level to avoid circular imports)
        from enviroflow_app.elt.transform.from_projects_data import Projects_Data
        from enviroflow_app.elt.transform.from_projects_dict import From_Project_Dicts

        # Build enriched projects dictionary using Projects_Data
        projects_data_processor = Projects_Data(
            projects_df=projects,
            jobs_df=jobs_analytics,
            quotes_df=quotes,
            labour_hours_df=labour_hours,
            costs_df=costs,
        )
        projects_dict = projects_data_processor.projects_dict

        console.print("📊 Converting enriched projects to analytics table...")
        projects_analytics_processor = From_Project_Dicts(projects=projects_dict)
        projects_analytics_df = projects_analytics_processor.projects_table

        # Save analytics table using _save_dataframe (MotherDuck/local)
        # config should be passed from caller
        _save_dataframe(projects_analytics_df, "projects_for_analytics", config)

        console.print(
            "✅ [bold green]Projects analytics table built successfully![/bold green]"
        )
        console.print("📊 Summary:")
        console.print(f"  • Analytics projects: {len(projects_analytics_df)} records")
        console.print(f"  • Source projects: {len(projects_dict)} enriched objects")
        console.print(f"  • Columns: {len(projects_analytics_df.columns)}")

        # Calculate some interesting stats
        if "total_quote_value" in projects_analytics_df.columns:
            total_value = projects_analytics_df["total_quote_value"].sum()
            console.print(f"  • Total project value: ${total_value:,.2f}")

        if "gross_profit" in projects_analytics_df.columns:
            total_profit = projects_analytics_df["gross_profit"].sum()
            console.print(f"  • Total gross profit: ${total_profit:,.2f}")

        return {"projects_for_analytics": projects_analytics_df}

    except Exception as e:
        console.print(
            f"❌ [bold red]Projects analytics building failed:[/bold red] {e}"
        )
        raise
