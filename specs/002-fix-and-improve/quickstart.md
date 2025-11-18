# Quickstart: Data Pipeline GUI Controller

## Quick Setup

### Prerequisites
- Python 3.10+ environment with Poetry
- MotherDuck credentials configured in `.streamlit/secrets.toml`
- Trello, Float, and Google Sheets API credentials configured
- Existing Enviroflow App codebase with CLI pipeline working

### 1. Verify CLI Pipeline Works

Before implementing the GUI, ensure the CLI pipeline executes successfully:

```bash
# Activate environment
poetry shell

# Test individual operations
python -m enviroflow_app.cli.main extract trello
python -m enviroflow_app.cli.main transform quotes

# Test full pipeline
python -m enviroflow_app.cli.main run-all

# Verify data in MotherDuck
python -c "
from enviroflow_app.elt.motherduck import md
import streamlit as st
conn = md.MotherDuck(st.secrets['motherduck']['token'], 'enviroflow')
print(conn.conn.execute('SHOW TABLES').pl())
"
```

Expected output: List of tables including `job_cards`, `labour_hours`, `quotes`, etc.

### 2. Check Credentials

Verify `.streamlit/secrets.toml` has all required credentials:

```toml
[motherduck]
token = "your_motherduck_token"
db = "enviroflow"

[trello]
api_key = "your_trello_api_key"
api_token = "your_trello_api_token"

[float]
api_key = "your_float_api_key"

[google_sheets]
credentials_path = "path/to/service-account.json"
```

### 3. Run the Streamlit App

```bash
# Launch app
streamlit run enviroflow_app/🏠_Home.py

# Navigate to Data Loading page:
# Click "🚚 Data Loading ELT" in sidebar
```

## Testing Checklist for Developers

When implementing or reviewing this feature, verify the following measurable criteria:

### Visual Design Criteria
- ✅ **"Prominent" button** = "Run Full Pipeline" button uses `st.button()` with colored background (primary=True), minimum 200px width, positioned top of left column
- ✅ **"Clear" description** = Button description tested with 3+ non-technical users who can explain what it does without additional documentation
- ✅ **"Easy" visual scanning** = Users can identify log message level (info/success/warning/error) in <2 seconds by color alone (blue/green/yellow/red)
- ✅ **Two-column layout** = Control panel occupies 33% width (1/3), feedback panel occupies 67% width (2/3), verified at 1920x1080 and 768x1024 resolutions

### Functional Testing Checklist
- ✅ MotherDuck connection status displays correctly (green checkmark or red X)
- ✅ "Run Full Pipeline" button disabled when operation running
- ✅ Real-time log messages appear with correct color coding
- ✅ Summary card shows all required metrics after completion
- ✅ Copy Results button produces valid Markdown
- ✅ Table list populates after pipeline completes
- ✅ Table preview shows first 100 rows
- ✅ PyGWalker explorer opens and displays data correctly
- ✅ Error messages are user-friendly (no raw stack traces in main display)
- ✅ Layout remains functional at tablet resolution (768px width)

---

## First-Time User Experience

### Running Your First Pipeline Operation

1. **Open the Data Loading page**
   - Navigate to "🚚 Data Loading ELT" in the sidebar
   - You'll see a two-column layout: controls on left, feedback on right

2. **Check Connection Status**
   - Top of page shows MotherDuck connection status
   - Should show: "✅ Connected to MotherDuck: enviroflow"
   - If red ❌: Check credentials and database connection

3. **Run a Single Operation**
   - In the "Extract" section, click **"Extract Trello Data"**
   - Watch the feedback panel for real-time log messages:
     ```
     🔵 14:30:15 - Connecting to Trello API...
     🔵 14:30:18 - Fetching boards...
     🔵 14:30:22 - Fetching job cards...
     ✅ 14:30:42 - Extracted 247 job cards
     ✅ 14:30:42 - Saved to MotherDuck table: job_cards
     ```
   - After completion, see summary card with:
     - Operation name and duration
     - Records processed
     - Tables created
     - "Copy Results" button

4. **Copy Results for Reporting**
   - Click "Copy Results" button
   - Paste into Slack, email, or document
   - Example copied text:
     ```
     ## Pipeline Execution Summary
     Operation: Extract Trello Data
     Status: ✅ Success
     Duration: 27.3 seconds
     Records Processed: 247 job cards

     ### Results
     - Extracted: 247 job cards
     - Saved to: MotherDuck table 'job_cards'
     ```

5. **Explore the Data**
   - After operation completes, "Explore Results" button appears
   - Click to open PyGWalker interactive data explorer
   - View first 100 rows, create charts, filter data
   - (Same interface as Data Explorer page)

### Running the Full Pipeline

1. **Click "Run Full Pipeline" button** (top of control panel)
   - Executes all operations in correct dependency order
   - Estimated time: 2-5 minutes
   - Watch progress in real-time

2. **Monitor Execution**
   - See each operation as it runs
   - Log messages show progress through pipeline stages:
     - Extract operations run first (in parallel where possible)
     - Transform operations run after extractions complete
     - Validation runs last

3. **Review Final Summary**
   - Consolidated report shows:
     - Total duration
     - All tables created/updated
     - Any warnings or errors
     - Record counts for each table

4. **Explore Updated Data**
   - Use "View Available Tables" section
   - Select any table to preview or explore
   - Data is now fresh in MotherDuck for all app pages

## Common Workflows

### Daily Data Refresh

**Goal**: Update all data from sources at start of workday

```
1. Open Data Loading page
2. Click "Run Full Pipeline"
3. Get coffee ☕ (takes ~3 minutes)
4. Review summary for any warnings
5. Navigate to Project Performance or other analysis pages
```

### Investigating Data Issues

**Goal**: Refresh specific data source that seems stale

```
1. Identify which data needs updating (e.g., Trello jobs)
2. Run just that extract operation (e.g., "Extract Trello Data")
3. Check log for any errors or warnings
4. If issues found, copy error details for troubleshooting
5. Retry or contact support with copied error information
```

### Verifying Pipeline Changes

**Goal**: Test pipeline after code changes

```
1. Run individual operations to test specific changes
2. Monitor logs for expected behavior
3. Check validation results
4. Explore resulting tables to verify data quality
5. Run full pipeline to test end-to-end integration
```

## Troubleshooting

### "Pipeline operation already running"

**Problem**: Tried to start operation while another is running

**Solution**:
- Wait for current operation to complete
- Check feedback panel for status
- If operation seems stuck (>10 minutes), refresh page

### "❌ Trello API connection failed"

**Problem**: Cannot connect to Trello

**Solutions**:
1. Check `.streamlit/secrets.toml` has correct Trello credentials
2. Verify API token hasn't expired (regenerate in Trello settings)
3. Check internet connection
4. Click "Retry" button in error message

### "⚠️ MotherDuck unavailable, saving to local files"

**Problem**: Cannot connect to MotherDuck cloud database

**Impact**: Data saved locally but not accessible to other app pages

**Solutions**:
1. Check `.streamlit/secrets.toml` has correct MotherDuck token
2. Verify MotherDuck service is operational (https://motherduck.com/status)
3. Check internet connection
4. After connection restored, re-run operation to upload to cloud

### "⚠️ Some validation checks failed"

**Problem**: Data quality issues detected

**Not necessarily an error**: Pipeline completed successfully, but data has warnings

**Actions**:
1. Expand validation details in feedback panel
2. Review specific warnings (e.g., "5 records missing quote_ref")
3. Determine if acceptable or needs investigation
4. Copy validation report for team review

### Operation Takes Longer Than Expected

**Normal durations**:
- Extract Trello: 20-60 seconds (depends on # of cards)
- Extract Float: 30-90 seconds (depends on date range)
- Extract Xero: 60-120 seconds (13K+ records from Google Sheets)
- Extract Sales: 60-120 seconds (30K+ records from Google Sheets)
- Transform operations: 5-30 seconds each
- Validation: 30-60 seconds

**If significantly longer**:
- Check internet connection speed
- API rate limits may be in effect (Trello, Float)
- Large data volumes (check record counts in logs)
- Wait for operation to complete naturally

### Page Won't Load or Crashes

**Solutions**:
1. Refresh page (Ctrl+R or Cmd+R)
2. Clear browser cache
3. Check browser console for errors (F12)
4. Restart Streamlit server:
   ```bash
   # Stop server (Ctrl+C)
   # Restart
   streamlit run enviroflow_app/🏠_Home.py
   ```

## Advanced Usage

### Copying Log History

To copy entire execution log (not just summary):

1. Scroll through feedback panel to review all messages
2. Use browser's text selection to select log messages
3. Copy and paste into support ticket or documentation
4. Includes timestamps for debugging

### Exploring Specific Table

After any operation:

1. Scroll to "Available Tables" section
2. Click dropdown to select table
3. See metadata: row count, column count, last updated
4. Click "Preview" to see first 100 rows
5. Click "Explore with PyGWalker" for full interactive analysis

### Running Operations Out of Order

The GUI warns about dependencies:

- ❌ Cannot run "Build Jobs Table" before "Extract Trello Data"
- Button will be disabled with tooltip explaining dependency
- Run prerequisites first, then dependent operations enable

## Integration with Other Pages

After running pipeline operations:

- **Project Performance**: Uses `projects_for_analytics` table (updated by full pipeline)
- **Subcontract Generator**: Uses `quotes` and `jobs_for_analytics` tables
- **Data Explorer**: Can query any tables created by pipeline
- **Project Name Checker**: Uses `projects` table

**Best Practice**: Run full pipeline daily to keep all app pages in sync.

## Next Steps

Once comfortable with the GUI:

1. **Schedule Regular Updates**: Run full pipeline each morning
2. **Monitor Data Quality**: Review validation warnings weekly
3. **Explore Data**: Use PyGWalker integration to understand business metrics
4. **Report Issues**: Copy error details when problems occur

## Getting Help

If you encounter issues:

1. **Copy error details** using "Copy Results" or by selecting log messages
2. **Include**: Operation name, error message, timestamp
3. **Check troubleshooting section** above
4. **Contact support** with copied information for faster resolution

## Testing Checklist

For developers testing the implementation:

- [ ] All 10+ operation buttons render correctly
- [ ] Can execute individual extract operations
- [ ] Can execute individual transform operations
- [ ] Can run full pipeline end-to-end
- [ ] Real-time logs appear during execution
- [ ] Summary card displays after completion
- [ ] "Copy Results" button copies formatted text
- [ ] Error handling shows clear messages
- [ ] Dependency checks prevent invalid operation order
- [ ] PyGWalker exploration works after operations
- [ ] Multiple operations can be run sequentially (not concurrently)
- [ ] Page state persists across reruns
- [ ] No console errors in browser dev tools
- [ ] **Visual verification: Two-column layout renders correctly in browser**
- [ ] **Visual verification: Color-coded logs display properly (blue/green/yellow/red)**
- [ ] **Visual verification: Buttons are clickable and interactive**
- [ ] **Visual verification: Layout adapts correctly on tablet-sized viewports (768px width)**
- [ ] **Visual verification: Feedback panel scrolls and updates in real-time**
- [ ] **Visual verification: All text is readable and properly sized**

### Browser Testing Instructions

After implementing UI changes:

1. **Launch the app**:
   ```bash
   streamlit run enviroflow_app/🏠_Home.py
   ```

2. **Open browser developer tools** (F12 or Right-click → Inspect)
   - Check Console tab for JavaScript errors
   - Check Network tab for failed requests

3. **Desktop testing** (1920x1080 or similar):
   - Verify two-column layout is balanced
   - Check that all buttons are visible and accessible
   - Confirm feedback panel has adequate space
   - Test clicking all interactive elements

4. **Tablet testing** (resize to ~768px width):
   - Resize browser window to tablet width
   - Verify layout remains usable
   - Check that columns don't overlap
   - Confirm all content is still accessible

5. **Interaction testing**:
   - Click "Run Full Pipeline" - verify spinner appears
   - Monitor log messages - verify they appear in real-time
   - Check color coding - blue (info), green (success), yellow (warning), red (error)
   - Test "Copy Results" - verify clipboard contains formatted text
   - Click "Explore Results" - verify PyGWalker loads

6. **Document any issues found**:
   - Screenshot visual problems
   - Note browser console errors
   - Record steps to reproduce issues

---

**Quickstart Version**: 1.0
**Last Updated**: October 2, 2025
**Maintainer**: Enviroflow Development Team
