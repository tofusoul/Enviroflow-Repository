"""
Example usage of the Google Sheets module.

This script demonstrates how to use the modern Google Sheets client
for accessing spreadsheets with async operations.
"""

import asyncio
import streamlit as st
from .gsheets import GoogleSheetsClient


async def main():
    """Main example function."""
    print("🚀 Google Sheets Module Example")
    print("=" * 50)

    # Initialize client (will automatically use Streamlit secrets)
    client = GoogleSheetsClient()

    # Example 1: List all accessible spreadsheets
    print("\n📋 Listing accessible spreadsheets...")
    try:
        spreadsheets = await client.list_spreadsheets()
        print(f"Found {len(spreadsheets)} spreadsheets:")
        for sheet in spreadsheets[:5]:  # Show first 5
            print(f"  - {sheet.title} ({sheet.spreadsheet_id})")
            print(f"    URL: {sheet.url}")
            print(f"    Sheets: {[s.name for s in sheet.sheets]}")
    except Exception as e:
        print(f"Error listing spreadsheets: {e}")

    # Example 2: Search for specific spreadsheets
    print("\n🔍 Searching for spreadsheets...")
    try:
        search_results = await client.search_spreadsheets("project")
        print(f"Found {len(search_results)} spreadsheets containing 'project':")
        for sheet in search_results:
            print(f"  - {sheet.title}")
    except Exception as e:
        print(f"Error searching spreadsheets: {e}")

    # Example 3: Get spreadsheet info
    print("\n📊 Getting spreadsheet information...")
    # You would replace this with an actual spreadsheet ID or URL
    # example_spreadsheet_id = "your-spreadsheet-id-here"
    # try:
    #     info = await client.get_spreadsheet_info(example_spreadsheet_id)
    #     print(f"Spreadsheet: {info.title}")
    #     print(f"URL: {info.url}")
    #     print(f"Sheets: {[s.name for s in info.sheets]}")
    # except Exception as e:
    #     print(f"Error getting spreadsheet info: {e}")

    # Example 4: Get sheet data as raw data
    print("\n📄 Getting sheet data...")
    # You would replace this with actual spreadsheet ID and sheet name
    # try:
    #     data = await client.get_sheet_data(
    #         spreadsheet_id=example_spreadsheet_id,
    #         sheet_name="Sheet1"
    #     )
    #     print(f"Retrieved {len(data)} rows")
    #     if data:
    #         print(f"Headers: {data[0]}")
    #         print(f"First row: {data[1] if len(data) > 1 else 'No data'}")
    # except Exception as e:
    #     print(f"Error getting sheet data: {e}")

    # Example 5: Get sheet as DataFrame
    print("\n🐼 Getting sheet as DataFrame...")
    # try:
    #     df = await client.get_sheet_as_dataframe(
    #         spreadsheet_id=example_spreadsheet_id,
    #         sheet_name="Sheet1",
    #         engine="pandas"
    #     )
    #     print(f"DataFrame shape: {df.shape}")
    #     print(f"Columns: {list(df.columns)}")
    #     print(f"First few rows:\n{df.head()}")
    # except Exception as e:
    #     print(f"Error getting DataFrame: {e}")

    # Example 6: Get all sheets as DataFrames
    print("\n📚 Getting all sheets as DataFrames...")
    # try:
    #     all_dfs = await client.get_all_sheets_as_dataframes(
    #         spreadsheet_id=example_spreadsheet_id,
    #         engine="pandas"
    #     )
    #     print(f"Retrieved {len(all_dfs)} sheets:")
    #     for sheet_name, df in all_dfs.items():
    #         print(f"  - {sheet_name}: {df.shape[0]} rows, {df.shape[1]} columns")
    # except Exception as e:
    #     print(f"Error getting all sheets: {e}")

    # Example 7: Using convenience functions
    print("\n⚡ Using convenience functions...")
    # try:
    #     # Quick access to sheet data
    #     data = await get_sheet_data(example_spreadsheet_id, "Sheet1")
    #     print(f"Quick data access: {len(data)} rows")
    #
    #     # Quick access to DataFrame
    #     df = await get_sheet_as_dataframe(example_spreadsheet_id, "Sheet1")
    #     print(f"Quick DataFrame access: {df.shape}")
    #
    #     # Quick list of spreadsheets
    #     sheets = await list_accessible_spreadsheets()
    #     print(f"Quick spreadsheet list: {len(sheets)} sheets")
    # except Exception as e:
    #     print(f"Error with convenience functions: {e}")

    print("\n✅ Example completed!")


def streamlit_example():
    """Streamlit example for the Google Sheets module."""
    st.title("📊 Google Sheets Integration Example")

    # Initialize client
    client = GoogleSheetsClient()

    # Sidebar for controls
    st.sidebar.header("Controls")

    # List spreadsheets
    if st.sidebar.button("List Accessible Spreadsheets"):
        with st.spinner("Loading spreadsheets..."):
            try:
                spreadsheets = asyncio.run(client.list_spreadsheets())
                st.success(f"Found {len(spreadsheets)} spreadsheets")

                for sheet in spreadsheets:
                    with st.expander(f"📋 {sheet.title}"):
                        st.write(f"**ID:** {sheet.spreadsheet_id}")
                        st.write(f"**URL:** {sheet.url}")
                        st.write(f"**Sheets:** {[s.name for s in sheet.sheets]}")
            except Exception as e:
                st.error(f"Error: {e}")

    # Search spreadsheets
    search_query = st.sidebar.text_input("Search spreadsheets", "project")
    if st.sidebar.button("Search"):
        with st.spinner("Searching..."):
            try:
                results = asyncio.run(client.search_spreadsheets(search_query))
                st.success(f"Found {len(results)} results")

                for sheet in results:
                    st.write(f"📄 {sheet.title}")
            except Exception as e:
                st.error(f"Error: {e}")

    # Main area for data display
    st.header("Data Access")

    # Input for spreadsheet ID/URL
    spreadsheet_input = st.text_input(
        "Enter Spreadsheet ID or URL",
        placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    )

    if spreadsheet_input:
        # Get spreadsheet info
        with st.spinner("Loading spreadsheet info..."):
            try:
                info = asyncio.run(client.get_spreadsheet_info(spreadsheet_input))
                st.success(f"📊 {info.title}")
                st.write(f"**URL:** {info.url}")

                # Sheet selector
                sheet_names = [s.name for s in info.sheets]
                selected_sheet = st.selectbox("Select Sheet", sheet_names)

                if selected_sheet:
                    # Get sheet data
                    if st.button("Load Sheet Data"):
                        with st.spinner("Loading data..."):
                            try:
                                df = asyncio.run(
                                    client.get_sheet_as_dataframe(
                                        spreadsheet_input,
                                        selected_sheet,
                                        engine="pandas",
                                    )
                                )
                                st.success(f"Loaded {len(df)} rows")
                                st.dataframe(df)

                                # Show info
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Rows", len(df))
                                with col2:
                                    st.metric("Columns", len(df.columns))

                            except Exception as e:
                                st.error(f"Error loading data: {e}")

            except Exception as e:
                st.error(f"Error: {e}")


if __name__ == "__main__":
    # Run the async example
    asyncio.run(main())

    # For Streamlit, you would use:
    # streamlit_example()
