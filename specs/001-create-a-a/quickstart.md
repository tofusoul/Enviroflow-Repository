# Quickstart: Streamlit Data Management Interface

## Quick Setup

### Prerequisites
- Python 3.10+ environment with Poetry
- MotherDuck credentials configured in `.streamlit/secrets.toml`
- Existing Enviroflow App codebase

### 1. Database Access

No additional database setup is required - the interface uses existing MotherDuck tables and connections.

### 2. Install Dependencies

The interface uses existing dependencies. Ensure PyGWalker is available:

```bash
poetry add pygwalker
```

### 3. Run the Application

```bash
# Activate environment
poetry shell

# Launch Streamlit app
streamlit run enviroflow_app/🏠_Home.py

# Navigate to the data management pages:
# - "🚚 Data Loading ELT" for pipeline operations
# - "🔮 Data Explorer" for data browsing and queries
```

## Using the Data Management Interface

### 1. ELT Pipeline Execution

1.  **Navigate to Data Loading ELT**: Click on "🚚 Data Loading ELT" in the sidebar
2.  **Configure Pipeline**: Select pipeline type (full/extraction/transform), output destination, and validation options
3.  **Run Operations**:
    - Use individual operation buttons for specific tasks (extract Trello data, build quotes table, etc.)
    - Or click "🚀 Execute Full Pipeline" for complete ELT processing
4.  **Monitor Progress**: Watch real-time feedback in the right panel, including execution logs and status updates
5.  **View Results**: Successful operations are tracked in execution history

### 2. Data Exploration

1.  **Navigate to Data Explorer**: Click on "🔮 Data Explorer" in the sidebar
2.  **Browse Business Tables**:
    - Select from predefined business tables (Trello Cards, Jobs, Projects, Quotes, Labour Hours)
    - Data loads automatically with PyGWalker integration for interactive exploration
3.  **Run Predefined Queries**:
    - Choose from available queries in the dropdown
    - Provide template variables if required (e.g., quote numbers, date ranges)
    - View results in an interactive table
4.  **Export Data**: Click "Download as CSV" to save current table data

### 3. Available Business Tables

| Display Name | Table Name | Description |
|-------------|------------|-------------|
| Trello Cards | `job_cards` | Individual job records with status and progress |
| Jobs | `jobs_for_analytics` | Processed job data for business reporting |
| Projects Raw | `projects` | High-level project information |
| Projects With Labour and Costs | `projects_for_analytics` | Projects with key metrics |
| Quotes | `quotes` | Customer quotations and proposals |
| Labour Hours | `labour_hours` | Employee time tracking records |

### 4. Predefined Queries

The system includes several business-focused queries:

- **Approved Jobs List**: Jobs with EQC approval dates
- **Jobs Awaiting Approval**: Jobs pending approval
- **Declined Jobs List**: Rejected jobs
- **Recent Quotes** (Template): Quotes after a specified quote number
- **Projects Analytics Formatted**: Full projects table with formatted dates
- **Jobs by EQC Approval Date** (Template): Jobs filtered by approval date range

## Testing Your Setup

### Manual Validation Steps

1. **Pipeline Execution**: Run individual extraction operations and verify data appears in MotherDuck
2. **Data Explorer**: Load each business table and verify PyGWalker interface works
3. **Query Execution**: Run both simple and templated queries, verify results display correctly
4. **CSV Export**: Test downloading data from both table browsing and query results
5. **Error Handling**: Test with invalid template variables or connection issues

### Expected Behavior

✅ **Pipeline Operations**: Individual buttons execute specific operations with real-time feedback
✅ **Data Tables**: All business tables load and display with PyGWalker exploration tools
✅ **Query Dropdown**: Shows all available predefined queries, sorted appropriately
✅ **Template Variables**: Input fields appear automatically for templated queries
✅ **Results Display**: Data appears in interactive tables with editing capabilities
✅ **CSV Download**: Exports work for both browsed tables and query results

### Troubleshooting

**Pipeline operations not working:**
- Check MotherDuck connection in secrets.toml
- Verify pipeline configuration and permissions
- Check execution logs for specific error messages

**Data tables not loading:**
- Verify MotherDuck credentials and database access
- Check table names exist: `SHOW TABLES;`
- Ensure PyGWalker is properly installed

**Queries failing:**
- Verify query files exist in `enviroflow_app/db_queries/`
- Check template variable syntax if applicable
- Test queries directly in MotherDuck console

**PyGWalker not working:**
- Ensure pygwalker package is installed
- Check browser console for JavaScript errors
- Try refreshing the page

## Running Tests

### Unit Tests
```bash
pytest tests/unit/test_query_helpers.py -v
```

### Integration Tests
```bash
pytest tests/integration/test_motherduck_integration.py -v
pytest tests/integration/test_sql_query_explorer.py -v
```

### Full Test Suite
```bash
pytest tests/ -k "query_explorer or motherduck" -v
```

## Next Steps

After verifying basic functionality:

1. **Add More Predefined Queries**: Create `.sql` and `.sql.j2` files in `enviroflow_app/db_queries/`
2. **Customize Business Tables**: Modify table definitions in the Data Explorer page
3. **Enhance Error Handling**: Add more specific error messages and recovery options
4. **Performance Optimization**: Add query result caching for frequently accessed data

This quickstart guide should get you up and running with the Streamlit Data Management Interface in under 10 minutes!
