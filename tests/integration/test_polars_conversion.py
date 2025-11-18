#!/usr/bin/env python3
"""
Integration test to verify polars conversion fixes.
"""

import asyncio
import pytest

from enviroflow_app.gsheets import GoogleSheetsClient
import polars as pl


@pytest.mark.asyncio
async def test_polars_conversion_fix():
    """Test the polars conversion fix for Google Sheets integration."""
    print("🧪 Testing polars conversion fix...")

    client = GoogleSheetsClient()
    print("✅ Client initialized")

    # Find the P&L spreadsheet
    spreadsheets = await client.list_spreadsheets()
    pnl_spreadsheet = None

    for spreadsheet in spreadsheets:
        if "Project P&L Report" in spreadsheet.title:
            pnl_spreadsheet = spreadsheet
            break

    if not pnl_spreadsheet:
        pytest.skip("Project P&L Report not found")

    print(f"✅ Found: {pnl_spreadsheet.title}")

    # Test a few sheets
    info = await client.get_spreadsheet_info(pnl_spreadsheet.spreadsheet_id)

    for sheet in info.sheets[:3]:  # Test first 3 sheets
        print(f"\n📋 Testing sheet: {sheet.name}")

        # Test polars conversion
        df = await client.get_sheet_as_dataframe(
            pnl_spreadsheet.spreadsheet_id, sheet.name, engine="polars"
        )
        assert isinstance(df, pl.DataFrame)
        print(f"   ✅ Polars: {df.shape}")

        # Test table detection
        tables = await client.detect_table_ranges(
            pnl_spreadsheet.spreadsheet_id, sheet.name
        )
        if tables:
            print(f"   🔍 Found {len(tables)} tables")

            # Test loading first table
            if len(tables) > 0:
                df_table = await client.get_table_data_by_detection(
                    pnl_spreadsheet.spreadsheet_id,
                    sheet.name,
                    table_index=0,
                    engine="polars",
                )
                assert isinstance(df_table, pl.DataFrame)
                print(f"   ✅ Table loaded: {df_table.shape}")

    print("\n✅ Test complete!")


if __name__ == "__main__":
    # Allow running as a standalone script for debugging
    asyncio.run(test_polars_conversion_fix())
