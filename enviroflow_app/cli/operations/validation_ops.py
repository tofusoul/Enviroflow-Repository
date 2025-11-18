"""
Data validation operations for Enviroflow ELT pipeline.

Contains functions for validating data quality, schema consistency,
and business logic compliance throughout the pipeline.
"""

from pathlib import Path
from typing import Dict, Any

import polars as pl
from rich.console import Console

console = Console()


def validate_table_schema(
    df: pl.DataFrame, expected_columns: Dict[str, pl.DataType], table_name: str
) -> bool:
    """
    Validate that a DataFrame has the expected schema.

    Args:
        df: DataFrame to validate
        expected_columns: Dictionary mapping column names to expected data types
        table_name: Name of the table for error reporting

    Returns:
        True if schema is valid

    Raises:
        ValueError: If schema validation fails
    """
    console.print(f"🔍 Validating schema for table: [cyan]{table_name}[/cyan]")

    # Check for missing columns
    missing_columns = set(expected_columns.keys()) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Table '{table_name}' missing columns: {missing_columns}")

    # Check for unexpected columns (warn but don't fail)
    unexpected_columns = set(df.columns) - set(expected_columns.keys())
    if unexpected_columns:
        console.print(
            f"⚠️  Table '{table_name}' has unexpected columns: {unexpected_columns}"
        )

    # Check data types for expected columns
    type_mismatches = []
    for col_name, expected_type in expected_columns.items():
        if col_name in df.columns:
            actual_type = df[col_name].dtype
            if actual_type != expected_type:
                type_mismatches.append(
                    f"{col_name}: expected {expected_type}, got {actual_type}"
                )

    if type_mismatches:
        console.print(f"⚠️  Type mismatches in '{table_name}':")
        for mismatch in type_mismatches:
            console.print(f"    {mismatch}")
        # For now, warn but don't fail on type mismatches
        # This can be made stricter as schemas stabilize

    console.print(f"✅ Schema validation passed for '{table_name}'")
    return True


def validate_job_cards(job_cards: pl.DataFrame) -> Dict[str, Any]:
    """
    Validate job cards data quality and completeness.

    Args:
        job_cards: Job cards DataFrame from Trello extraction

    Returns:
        Dictionary containing validation results and statistics
    """
    console.print("🔍 [bold blue]Validating job cards data...[/bold blue]")

    validation_results = {
        "total_records": len(job_cards),
        "validation_passed": True,
        "warnings": [],
        "errors": [],
    }

    try:
        # Basic data quality checks
        if len(job_cards) == 0:
            validation_results["errors"].append("Job cards table is empty")
            validation_results["validation_passed"] = False
            return validation_results

        # Check for required columns
        required_columns = ["card_title", "card_id", "board_name"]
        for col in required_columns:
            if col not in job_cards.columns:
                validation_results["errors"].append(f"Missing required column: {col}")
                validation_results["validation_passed"] = False

        # Check for job pattern in card titles
        if "card_title" in job_cards.columns:
            job_pattern_count = job_cards.filter(
                pl.col("card_title").str.contains(r"^\d")
            ).shape[0]

            validation_results["job_pattern_matches"] = job_pattern_count
            job_pattern_pct = (job_pattern_count / len(job_cards)) * 100

            if job_pattern_pct < 50:
                validation_results["warnings"].append(
                    f"Only {job_pattern_pct:.1f}% of cards match job pattern (start with digit)"
                )

        # Check for duplicates
        if "card_id" in job_cards.columns:
            duplicate_count = len(job_cards) - job_cards["card_id"].n_unique()
            validation_results["duplicate_cards"] = duplicate_count

            if duplicate_count > 0:
                validation_results["warnings"].append(
                    f"Found {duplicate_count} duplicate card IDs"
                )

        console.print("✅ Job cards validation complete")

    except Exception as e:
        validation_results["errors"].append(f"Validation error: {e}")
        validation_results["validation_passed"] = False

    return validation_results


def validate_quotes(quotes: pl.DataFrame) -> Dict[str, Any]:
    """
    Validate quotes data quality and business logic.

    Args:
        quotes: Unified quotes DataFrame

    Returns:
        Dictionary containing validation results and statistics
    """
    console.print("🔍 [bold blue]Validating quotes data...[/bold blue]")

    validation_results = {
        "total_records": len(quotes),
        "validation_passed": True,
        "warnings": [],
        "errors": [],
    }

    try:
        if len(quotes) == 0:
            validation_results["errors"].append("Quotes table is empty")
            validation_results["validation_passed"] = False
            return validation_results

        # Check required columns
        required_columns = ["quote_no", "customer", "line_total", "quote_source"]
        for col in required_columns:
            if col not in quotes.columns:
                validation_results["errors"].append(f"Missing required column: {col}")
                validation_results["validation_passed"] = False

        # Business logic validations
        if "line_total" in quotes.columns:
            # Check for negative values - these are credit notes
            negative_count = quotes.filter(pl.col("line_total") < 0).shape[0]
            validation_results["negative_line_totals"] = negative_count

            if negative_count > 0:
                negative_pct = (negative_count / len(quotes)) * 100
                validation_results["warnings"].append(
                    f"Found {negative_count} ({negative_pct:.2f}%) credit notes (negative line totals)"
                )

            # Check for zero values
            zero_count = quotes.filter(pl.col("line_total") == 0).shape[0]
            validation_results["zero_line_totals"] = zero_count

            if zero_count > 0:
                zero_pct = (zero_count / len(quotes)) * 100
                validation_results["warnings"].append(
                    f"Found {zero_count} ({zero_pct:.2f}%) zero value line items"
                )

        # Check quote source distribution
        if "quote_source" in quotes.columns:
            source_counts = quotes.group_by("quote_source").len()
            validation_results["source_distribution"] = source_counts.to_dicts()

            # Warn if heavily skewed towards one source
            total_quotes = len(quotes)
            for row in source_counts.iter_rows(named=True):
                source_pct = (row["len"] / total_quotes) * 100
                if source_pct > 95:
                    validation_results["warnings"].append(
                        f"Quotes heavily skewed towards {row['quote_source']} ({source_pct:.1f}%)"
                    )

        console.print("✅ Quotes validation complete")

    except Exception as e:
        validation_results["errors"].append(f"Validation error: {e}")
        validation_results["validation_passed"] = False

    return validation_results


def validate_pipeline_consistency(processed_data_dir: Path) -> Dict[str, Any]:
    """
    Validate consistency across all pipeline outputs.

    Args:
        processed_data_dir: Directory containing processed Parquet files

    Returns:
        Dictionary containing cross-table validation results
    """
    console.print("🔍 [bold blue]Validating pipeline consistency...[/bold blue]")

    validation_results = {
        "validation_passed": True,
        "cross_table_checks": {},
        "warnings": [],
        "errors": [],
    }

    try:
        # Load key tables
        tables = {}
        expected_files = [
            "job_cards.parquet",
            "quotes.parquet",
            "jobs.parquet",
            "projects.parquet",
        ]

        for file_name in expected_files:
            file_path = processed_data_dir / file_name
            if file_path.exists():
                table_name = file_name.replace(".parquet", "")
                tables[table_name] = pl.read_parquet(file_path)
                console.print(
                    f"📖 Loaded {table_name}: {len(tables[table_name])} records"
                )
            else:
                validation_results["warnings"].append(
                    f"Table file not found: {file_name}"
                )

        # Cross-table consistency checks
        if "job_cards" in tables and "jobs" in tables:
            job_cards_count = len(tables["job_cards"])
            jobs_count = len(tables["jobs"])

            # Jobs should be a subset of job cards (after filtering)
            if jobs_count > job_cards_count:
                validation_results["errors"].append(
                    f"Jobs count ({jobs_count}) exceeds job cards count ({job_cards_count})"
                )
                validation_results["validation_passed"] = False

            # Calculate conversion rate
            conversion_rate = (
                (jobs_count / job_cards_count) * 100 if job_cards_count > 0 else 0
            )
            validation_results["cross_table_checks"]["job_conversion_rate"] = (
                conversion_rate
            )

            if conversion_rate < 50:
                validation_results["warnings"].append(
                    f"Low job conversion rate: {conversion_rate:.1f}% (jobs/job_cards)"
                )

        if "quotes" in tables and "jobs" in tables:
            quotes_customers = (
                tables["quotes"]["customer"].n_unique()
                if "customer" in tables["quotes"].columns
                else 0
            )
            jobs_customers = (
                tables["jobs"]["customer"].n_unique()
                if "customer" in tables["jobs"].columns
                else 0
            )

            validation_results["cross_table_checks"]["quotes_unique_customers"] = (
                quotes_customers
            )
            validation_results["cross_table_checks"]["jobs_unique_customers"] = (
                jobs_customers
            )

            # There should be reasonable overlap in customers
            if quotes_customers > 0 and jobs_customers > 0:
                customer_overlap_ratio = min(quotes_customers, jobs_customers) / max(
                    quotes_customers, jobs_customers
                )
                validation_results["cross_table_checks"]["customer_overlap_ratio"] = (
                    customer_overlap_ratio
                )

                if customer_overlap_ratio < 0.3:
                    validation_results["warnings"].append(
                        f"Low customer overlap between quotes and jobs: {customer_overlap_ratio:.2f}"
                    )

        console.print("✅ Pipeline consistency validation complete")

    except Exception as e:
        validation_results["errors"].append(f"Consistency validation error: {e}")
        validation_results["validation_passed"] = False

    return validation_results


def validate_business_logic(projects_analytics: pl.DataFrame) -> Dict[str, Any]:
    """
    Validate business logic in the final analytics table.

    Args:
        projects_analytics: Projects for analytics DataFrame

    Returns:
        Dictionary containing business logic validation results
    """
    console.print("🔍 [bold blue]Validating business logic...[/bold blue]")

    validation_results = {
        "total_projects": len(projects_analytics),
        "validation_passed": True,
        "business_logic_checks": {},
        "warnings": [],
        "errors": [],
    }

    try:
        if len(projects_analytics) == 0:
            validation_results["errors"].append("Projects analytics table is empty")
            validation_results["validation_passed"] = False
            return validation_results

        # Financial calculations validation
        financial_columns = [
            "total_quote_value",
            "labour_costs_total",
            "supplier_costs_total",
            "gross_profit",
        ]

        for col in financial_columns:
            if col in projects_analytics.columns:
                # Check for negative values where they shouldn't exist
                if col in [
                    "total_quote_value",
                    "labour_costs_total",
                    "supplier_costs_total",
                ]:
                    negative_count = projects_analytics.filter(pl.col(col) < 0).shape[0]
                    if negative_count > 0:
                        validation_results["warnings"].append(
                            f"Found {negative_count} negative values in {col}"
                        )

                # Check for extremely high values (potential data quality issues)
                if col == "total_quote_value":
                    max_value = projects_analytics[col].max()
                    if (
                        max_value is not None
                        and isinstance(max_value, (int, float))
                        and max_value > 10_000_000
                    ):  # $10M threshold
                        validation_results["warnings"].append(
                            f"Extremely high quote value detected: ${max_value:,.2f}"
                        )

        # Margin calculations
        if (
            "gross_profit" in projects_analytics.columns
            and "total_quote_value" in projects_analytics.columns
        ):
            # Calculate projects with negative margins
            projects_with_data = projects_analytics.filter(
                (pl.col("total_quote_value").is_not_null())
                & (pl.col("total_quote_value") > 0)
            )

            if len(projects_with_data) > 0:
                negative_margin_count = projects_with_data.filter(
                    pl.col("gross_profit") < 0
                ).shape[0]
                negative_margin_pct = (
                    negative_margin_count / len(projects_with_data)
                ) * 100

                validation_results["business_logic_checks"][
                    "negative_margin_projects"
                ] = negative_margin_count
                validation_results["business_logic_checks"][
                    "negative_margin_percentage"
                ] = negative_margin_pct

                if negative_margin_pct > 25:
                    validation_results["warnings"].append(
                        f"High percentage of negative margin projects: {negative_margin_pct:.1f}%"
                    )

        # Check for missing critical data
        if "labour_hours" in projects_analytics.columns:
            no_labour_count = projects_analytics.filter(
                (pl.col("labour_hours").is_null()) | (pl.col("labour_hours") == 0)
            ).shape[0]

            no_labour_pct = (no_labour_count / len(projects_analytics)) * 100
            validation_results["business_logic_checks"]["projects_without_labour"] = (
                no_labour_count
            )
            validation_results["business_logic_checks"][
                "projects_without_labour_pct"
            ] = no_labour_pct

            if no_labour_pct > 80:
                validation_results["warnings"].append(
                    f"High percentage of projects without labour data: {no_labour_pct:.1f}%"
                )

        console.print("✅ Business logic validation complete")

    except Exception as e:
        validation_results["errors"].append(f"Business logic validation error: {e}")
        validation_results["validation_passed"] = False

    return validation_results


def run_full_validation_suite(processed_data_dir: Path) -> Dict[str, Any]:
    """
    Run the complete validation suite on all pipeline outputs.

    Args:
        processed_data_dir: Directory containing processed Parquet files

    Returns:
        Comprehensive validation results
    """
    console.print("🔍 [bold blue]Running full validation suite...[/bold blue]")

    suite_results = {
        "overall_passed": True,
        "validations": {},
        "summary": {"total_errors": 0, "total_warnings": 0},
    }

    # Individual table validations
    table_validations = [
        ("job_cards", validate_job_cards),
        ("quotes", validate_quotes),
    ]

    for table_name, validation_func in table_validations:
        file_path = processed_data_dir / f"{table_name}.parquet"
        if file_path.exists():
            df = pl.read_parquet(file_path)
            validation_result = validation_func(df)
            suite_results["validations"][table_name] = validation_result

            if not validation_result["validation_passed"]:
                suite_results["overall_passed"] = False

            suite_results["summary"]["total_errors"] += len(
                validation_result.get("errors", [])
            )
            suite_results["summary"]["total_warnings"] += len(
                validation_result.get("warnings", [])
            )

    # Cross-table consistency validation
    consistency_result = validate_pipeline_consistency(processed_data_dir)
    suite_results["validations"]["pipeline_consistency"] = consistency_result

    if not consistency_result["validation_passed"]:
        suite_results["overall_passed"] = False

    suite_results["summary"]["total_errors"] += len(
        consistency_result.get("errors", [])
    )
    suite_results["summary"]["total_warnings"] += len(
        consistency_result.get("warnings", [])
    )

    # Business logic validation (if analytics table exists)
    analytics_file = processed_data_dir / "projects_for_analytics.parquet"
    if analytics_file.exists():
        analytics_df = pl.read_parquet(analytics_file)
        business_logic_result = validate_business_logic(analytics_df)
        suite_results["validations"]["business_logic"] = business_logic_result

        if not business_logic_result["validation_passed"]:
            suite_results["overall_passed"] = False

        suite_results["summary"]["total_errors"] += len(
            business_logic_result.get("errors", [])
        )
        suite_results["summary"]["total_warnings"] += len(
            business_logic_result.get("warnings", [])
        )

    # Print summary
    console.print("\n📊 [bold blue]Validation Suite Summary:[/bold blue]")
    console.print(
        f"  Overall Status: {'✅ PASSED' if suite_results['overall_passed'] else '❌ FAILED'}"
    )
    console.print(f"  Total Errors: {suite_results['summary']['total_errors']}")
    console.print(f"  Total Warnings: {suite_results['summary']['total_warnings']}")

    return suite_results
