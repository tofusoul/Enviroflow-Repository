#!/usr/bin/env python3
"""
Main CLI entry point for Enviroflow ELT pipeline.

This is the primary command-line interface for the Enviroflow data pipeline,
providing a simple, reliable CLI without complex framework dependencies.
"""

import sys
import traceback


def run_pipeline():
    """Run the actual pipeline logic."""
    try:
        from .config import OutputDestination, PipelineConfig
        from .dag import Pipeline

        print("🚀 Starting Enviroflow ELT Pipeline...")

        # Create default configuration
        config = PipelineConfig.create(
            destination=OutputDestination.MOTHERDUCK,
            validate=True,
            pipeline_type="full",
        )

        print("🎯 Running complete ELT pipeline...")
        engine = Pipeline.create_full_pipeline()
        engine.config = config

        print("📋 Executing pipeline...")
        engine.execute()

        print("✅ Pipeline completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        print("Traceback:")
        traceback.print_exc()
        return False


def show_help():
    """Show help message."""
    print("Enviroflow ELT Pipeline")
    print("Data extraction, transformation, and loading for business analytics")
    print("")
    print("Usage: python -m enviroflow_app.cli.main <command> [subcommand] [options]")
    print("")
    print("Commands:")
    print("  run-all         - Run the complete pipeline")
    print("  status          - Show pipeline status")
    print("  validate        - Run validation checks on pipeline data")
    print("  dag-info        - Show DAG structure and dependencies")
    print("  version         - Show version information")
    print("  extract         - Data extraction commands")
    print("  transform       - Data transformation commands")
    print("  load            - Data loading and persistence commands")
    print("  --help          - Show this help message")
    print("")
    print("Subcommands:")
    print(
        "  Use 'python -m enviroflow_app.cli.main <command> --help' for command-specific help"
    )


def run_validation():
    """Run validation checks on pipeline data."""
    try:
        from .operations.validation_ops import run_full_validation_suite
        from pathlib import Path

        print("🔍 Running Pipeline Validation...")
        processed_dir = Path("Data/cli_pipeline_data/processed_parquet")
        validation_results = run_full_validation_suite(processed_dir)

        if validation_results["overall_passed"]:
            print("✅ All validation checks passed!")
        else:
            print("⚠️ Some validation checks failed")
            print(f"Total errors: {validation_results['summary']['total_errors']}")
            print(f"Total warnings: {validation_results['summary']['total_warnings']}")
        return validation_results["overall_passed"]
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


def show_dag_info():
    """Show DAG structure and dependencies."""
    try:
        from .dag import Pipeline

        print("🔍 DAG Information: full pipeline")
        engine = Pipeline.create_full_pipeline()

        # Validate the DAG
        print("\n🔧 DAG Validation:")
        try:
            engine.validate()
            print("✅ DAG is valid - no cycles or missing dependencies")
        except Exception as e:
            print(f"❌ DAG validation failed: {e}")
            return False

        # Show execution order
        print("\n📋 Execution Order:")
        execution_order = engine._topological_sort()
        for i, task_name in enumerate(execution_order, 1):
            task = engine.tasks[task_name]
            deps = list(task.dependencies)
            dep_str = (
                f" (depends on: {', '.join(deps)})" if deps else " (no dependencies)"
            )
            print(f"  {i:>2}. {task_name}{dep_str}")

        # Show statistics
        print("\n📊 Pipeline Statistics:")
        print(f"Total Tasks: {len(engine.tasks)}")
        print(
            f"Tasks with Dependencies: {len([t for t in engine.tasks.values() if t.dependencies])}"
        )
        print(
            f"Root Tasks (no deps): {len([t for t in engine.tasks.values() if not t.dependencies])}"
        )

        return True
    except Exception as e:
        print(f"❌ DAG analysis failed: {e}")
        return False


def show_version():
    """Show version information."""
    print("🏠 Enviroflow ELT Pipeline")
    print("")
    print("Enviroflow CLI Pipeline")
    print("Version: 2.0.0 (Simplified architecture)")
    print("Date: September 2025")
    print("")
    print("Features:")
    print("• Simple, reliable CLI without complex dependencies")
    print("• Custom DAG orchestration system")
    print("• Comprehensive validation suite")
    print("• MotherDuck cloud data warehouse integration")
    print("")
    print("Pipeline Stages:")
    print("• Extract: Trello, Float, Xero/Google Sheets")
    print("• Transform: Quotes, Jobs, Customers, Labour, Projects, Analytics")
    print("• Load: File management, backup/restore, export")


def run_extract_command(subcommand):
    """Run individual extract operations."""
    try:
        from .dag import Pipeline
        from .config import OutputDestination, PipelineConfig

        if subcommand == "all":
            print("🚀 Running all extraction tasks...")
            config = PipelineConfig.create(
                destination=OutputDestination.MOTHERDUCK,
                validate=True,
                pipeline_type="extraction",
            )
            engine = Pipeline.create_extraction_pipeline()
            engine.config = config
            engine.execute()
        elif subcommand == "trello":
            print("🚀 Extracting Trello data...")
            from .operations.extraction_ops import extract_trello_data

            extract_trello_data()
            print("✅ Trello extraction completed successfully")
        elif subcommand == "float":
            print("🚀 Extracting Float data...")
            from .operations.extraction_ops import extract_float_data

            extract_float_data()
            print("✅ Float extraction completed successfully")
        elif subcommand == "xero-costs":
            print("🚀 Extracting Xero costs...")
            from .operations.extraction_ops import extract_xero_costs

            extract_xero_costs()
            print("✅ Xero costs extraction completed successfully")
        elif subcommand == "sales":
            print("🚀 Extracting sales data...")
            from .operations.extraction_ops import extract_sales_data

            extract_sales_data()
            print("✅ Sales extraction completed successfully")
        else:
            print(f"❌ Unknown extract subcommand: {subcommand}")
            print("Available: all, trello, float, xero-costs, sales")
            return False
        return True
    except Exception as e:
        print(f"❌ Extract operation failed: {e}")
        traceback.print_exc()
        return False


def run_transform_command(subcommand):
    """Run individual transform operations."""
    try:
        from .dag import Pipeline
        from .config import OutputDestination, PipelineConfig

        if subcommand == "all":
            print("🚀 Running all transformation tasks...")
            config = PipelineConfig.create(
                destination=OutputDestination.MOTHERDUCK,
                validate=True,
                pipeline_type="transform",
            )
            engine = Pipeline.create_transform_pipeline()
            engine.config = config
            engine.execute()
        elif subcommand == "quotes":
            print("🚀 Building quotes table...")
            from .operations.transform_ops import build_quotes_table

            build_quotes_table()
            print("✅ Quotes table built successfully")
        elif subcommand == "jobs":
            print("🚀 Building jobs table...")
            # Jobs table needs job_cards and quotes as input - this is more complex
            print(
                "⚠️  Jobs table requires job_cards and quotes inputs - use 'transform all' for full pipeline"
            )
        elif subcommand == "customers":
            print("🚀 Building customers table...")
            # Customers table needs job_cards as input
            print(
                "⚠️  Customers table requires job_cards input - use 'transform all' for full pipeline"
            )
        elif subcommand == "projects":
            print("🚀 Building projects table...")
            # Projects table needs jobs_with_hours and quotes as input
            print(
                "⚠️  Projects table requires jobs and quotes inputs - use 'transform all' for full pipeline"
            )
        else:
            print(f"❌ Unknown transform subcommand: {subcommand}")
            print("Available: all, quotes, jobs, customers, projects")
            return False
        return True
    except Exception as e:
        print(f"❌ Transform operation failed: {e}")
        traceback.print_exc()
        return False


def run_load_command(subcommand):
    """Run individual load operations."""
    try:
        if subcommand == "status":
            print("📊 Data Status:")
            from pathlib import Path

            dirs_to_check = [
                ("Raw JSON", "Data/cli_pipeline_data/raw_json"),
                ("Processed Parquet", "Data/cli_pipeline_data/processed_parquet"),
                ("P&L Data", "pnl_data"),
            ]
            for name, path in dirs_to_check:
                dir_path = Path(path)
                if dir_path.exists():
                    file_count = len(list(dir_path.glob("*")))
                    print(f"  ✅ {name:<20} {file_count:>3} files")
                else:
                    print(f"  ⚫ {name:<20} {'—':>3} (not found)")
        elif subcommand == "clean":
            print("🧹 Cleaning pipeline data...")
            from pathlib import Path
            import shutil

            processed_dir = Path("Data/cli_pipeline_data/processed_parquet")
            if processed_dir.exists():
                shutil.rmtree(processed_dir)
                processed_dir.mkdir(parents=True)
                print("✅ Processed data cleaned")
            else:
                print("⚫ No processed data to clean")
        else:
            print(f"❌ Unknown load subcommand: {subcommand}")
            print("Available: status, clean")
            return False
        return True
    except Exception as e:
        print(f"❌ Load operation failed: {e}")
        traceback.print_exc()
        return False


def run_subcommand(app_name, remaining_args):
    """Run subcommands with simplified implementations."""
    if not remaining_args:
        print(f"📋 {app_name.title()} Commands:")
        if app_name == "extract":
            print("  all         - Run all extraction tasks")
            print("  trello      - Extract Trello data")
            print("  float       - Extract Float data")
            print("  xero-costs  - Extract Xero costs")
            print("  sales       - Extract sales data")
        elif app_name == "transform":
            print("  all         - Run all transformation tasks")
            print("  quotes      - Build quotes table")
            print("  jobs        - Build jobs table")
            print("  customers   - Build customers table")
            print("  projects    - Build projects table")
        elif app_name == "load":
            print("  status      - Show data status")
            print("  clean       - Clean processed data")
        print("")
        print(f"Usage: python -m enviroflow_app.cli.main {app_name} <subcommand>")
        return True

    subcommand = remaining_args[0]

    if app_name == "extract":
        return run_extract_command(subcommand)
    elif app_name == "transform":
        return run_transform_command(subcommand)
    elif app_name == "load":
        return run_load_command(subcommand)
    else:
        print(f"❌ Unknown subcommand app: {app_name}")
        return False


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    command = sys.argv[1]

    if command in ("--help", "-h", "help"):
        show_help()
    elif command == "run-all":
        success = run_pipeline()
        sys.exit(0 if success else 1)
    elif command == "status":
        print("📊 Pipeline Status:")
        print("✅ CLI is available and ready")
        print("🔧 Configuration: Full pipeline with MotherDuck destination")
    elif command == "validate":
        success = run_validation()
        sys.exit(0 if success else 1)
    elif command == "dag-info":
        success = show_dag_info()
        sys.exit(0 if success else 1)
    elif command == "version":
        show_version()
    elif command in ("extract", "transform", "load"):
        # Pass remaining arguments to subcommand
        remaining_args = sys.argv[2:]
        success = run_subcommand(command, remaining_args)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown command: {command}")
        print("Use --help to see available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()
