#!/usr/bin/env python3
"""
Script to inspect actual P&L table structures for test suite validation.
This will help us get the real column names and layouts to fix test expectations.
"""

import asyncio
from enviroflow_app.gsheets import GoogleSheetsClient


async def inspect_pnl_tables():
    print("🔍 INSPECTING ACTUAL P&L TABLE STRUCTURES")
    print("=" * 60)

    client = GoogleSheetsClient()
    spreadsheet_id = "1-c_VsrnmDK7eOB3pRxjTP0f2v0qFanpFomNuZJktDoU"

    # Target tables from TODO
    target_tables = [
        "costs",
        "constants",
        "report_scope_projects",
        "xero_name",
        "sales",
        "quotes",
        "pricing_table",
    ]

    for table_name in target_tables:
        try:
            print(f"\n📊 TABLE: {table_name.upper()}")
            print("-" * 40)

            # Get spreadsheet info to check if sheet exists
            spreadsheet_info = await client.get_spreadsheet_info(spreadsheet_id)
            sheet_names = [sheet.name for sheet in spreadsheet_info.sheets]

            if table_name not in sheet_names:
                print(f'❌ Sheet "{table_name}" not found in spreadsheet')
                print(f"   Available sheets: {sheet_names[:10]}...")
                continue

            # Get sample data to inspect structure
            raw_data = await client.get_sheet_data(
                spreadsheet_id, table_name, range_name=f"{table_name}!1:10"
            )

            if not raw_data:
                print(f"❌ No data found in {table_name}")
                continue

            print(f"✅ Found {len(raw_data)} sample rows")

            # Analyze row structures
            for i, row in enumerate(raw_data[:5]):
                non_empty = sum(1 for cell in row if cell and str(cell).strip())
                print(f"   Row {i+1}: {len(row)} columns, {non_empty} non-empty")
                print(f"      First 8 cells: {row[:8]}")

            # Try to identify headers using our logic
            headers, _ = client._prepare_data_for_polars(raw_data)
            print(f"   Detected headers ({len(headers)} columns):")
            print(
                f"      {headers[:10]}..." if len(headers) > 10 else f"      {headers}"
            )

            # Get full table dimensions
            full_data = await client.get_sheet_data(spreadsheet_id, table_name)
            print(f"   Full table: {len(full_data)} rows total")

        except Exception as e:
            print(f"❌ Error inspecting {table_name}: {e}")

    print("\n🎯 Inspection complete! Use this data to update expectations.")


if __name__ == "__main__":
    asyncio.run(inspect_pnl_tables())
