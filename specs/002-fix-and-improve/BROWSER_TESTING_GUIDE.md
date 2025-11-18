# Browser UI Testing Guide - Data Pipeline GUI Controller

**Feature**: Data Pipeline GUI Controller
**Page**: 6_🚚_Data_Loading_ELT.py
**Date**: October 2, 2025
**Task**: T016 - Browser UI testing for layout and visual elements

---

## Overview

This document provides the manual browser testing checklist for verifying the Data Pipeline GUI Controller interface. All tests should be performed in a web browser after launching the Streamlit application.

## Prerequisites

1. **Launch Streamlit App**:
   ```bash
   cd /home/envirodev/Projects/Enviroflow_App
   poetry shell
   streamlit run enviroflow_app/🏠_Home.py
   ```

2. **Navigate to Page**: Click "🚚 Data Loading ELT" in the left sidebar

3. **Required Credentials**: Ensure `.streamlit/secrets.toml` has valid:
   - MotherDuck token and database
   - Trello API credentials
   - Float API credentials
   - Google Sheets credentials

---

## Test Scenarios

### 1. Layout and Visual Structure ✅

#### 1.1 Two-Column Layout
- [ ] **Control panel on left** (33% width)
- [ ] **Feedback panel on right** (67% width)
- [ ] Columns remain distinct and don't overlap
- [ ] Content flows naturally left-to-right
- [ ] Divider line between columns is visible

**Expected**: Clean two-column separation with control panel narrower than feedback panel

---

#### 1.2 Page Header
- [ ] Title displays: "🚚 Data Loading ELT Pipeline"
- [ ] Description visible below title
- [ ] Page icon (🚚) displays in browser tab
- [ ] Divider line separates header from content

**Expected**: Clear, prominent header with truck emoji

---

### 2. Connection Status Display ✅

#### 2.1 Successful Connection
- [ ] Green checkmark (✅) displays
- [ ] Message shows: "Connected to MotherDuck: `enviroflow`" (or your DB name)
- [ ] Status appears in green success box
- [ ] Connection check happens immediately on page load

**Expected**: `✅ Connected to MotherDuck: enviroflow` in green box

---

#### 2.2 Failed Connection
- [ ] Red X (❌) displays
- [ ] Message shows: "Connection Failed: Unable to connect to MotherDuck"
- [ ] Status appears in red error box
- [ ] "🔄 Retry Connection" button appears
- [ ] Clicking retry button re-checks connection

**Expected**: Clear error message with retry option

---

### 3. Run Full Pipeline Button ✅

#### 3.1 Button Appearance
- [ ] Button text: "🚀 Run Full Pipeline"
- [ ] Button is prominent (uses primary styling - blue background)
- [ ] Button is centered or left-aligned in control panel
- [ ] Description text appears below button:
  - "Refresh all data from Trello, Float, Xero, and Google Sheets."
  - "Updates all analytics tables."

**Expected**: Large, blue button with rocket emoji and clear description

---

#### 3.2 Button States
- [ ] **Enabled state**: Button clickable when connection is good and no pipeline running
- [ ] **Disabled state**: Button grayed out when:
  - Pipeline is already running
  - MotherDuck connection unavailable
- [ ] Tooltip or message explains why button is disabled (if applicable)

**Expected**: Button enabled only when safe to run pipeline

---

### 4. Real-Time Log Display ✅

#### 4.1 Log Streaming During Execution
- [ ] Logs appear in the feedback panel (right column)
- [ ] Each log entry has:
  - Emoji indicator (🔵/✅/⚠️/❌)
  - Timestamp (HH:MM:SS format)
  - Message text
- [ ] Log entries stack vertically (newest at bottom)
- [ ] Panel auto-scrolls to show latest message

**Expected**: Live log messages appearing as pipeline executes

---

#### 4.2 Color Coding (CRITICAL TEST)
- [ ] **🔵 Blue**: Info messages (connecting, fetching data)
- [ ] **✅ Green**: Success messages (extracted 247 records, saved to table)
- [ ] **⚠️ Yellow**: Warning messages (data quality warnings)
- [ ] **❌ Red**: Error messages (connection failed, operation error)
- [ ] Colors match Streamlit's standard palette
- [ ] Color-blind users can distinguish by emoji shape

**Testing Method**:
1. Run pipeline
2. Verify each log level appears with correct color
3. Time how fast you can identify error vs success (<2 seconds goal)

**Expected**: Clear visual distinction by both color and emoji

---

### 5. Progress Indication ✅

#### 5.1 Spinner Display
- [ ] Spinner appears when "Run Full Pipeline" is clicked
- [ ] Spinner message shows: "Pipeline running..."
- [ ] Spinner is visible in feedback panel
- [ ] Spinner disappears when pipeline completes

**Expected**: Animated spinner provides feedback during execution

---

#### 5.2 Status Indicator
- [ ] Shows current operation: "Run Full Pipeline"
- [ ] Shows elapsed time (updates if visible, or shown after completion)
- [ ] Status clears when operation completes

**Expected**: User knows what's running at any time

---

### 6. Execution Results Summary ✅

#### 6.1 Summary Card Display
- [ ] Summary appears after pipeline completes
- [ ] Card shows in feedback panel (right column)
- [ ] Uses colored box (green for success, red for error)
- [ ] Contains:
  - ✅ Operation name ("Run Full Pipeline")
  - ✅ Status badge (✅ Success / ❌ Error)
  - ✅ Duration in seconds (e.g., "125.4s")
  - ✅ List of tables created/updated
  - ✅ Number of tables (e.g., "47 tables available")

**Expected**: Clear, formatted summary with all key metrics

---

#### 6.2 Summary Formatting
- [ ] Markdown formatting renders correctly
- [ ] Bullet points align properly
- [ ] Table names display as code (monospace font)
- [ ] Duration formatted to 1 decimal place

**Expected**: Professional, readable summary format

---

### 7. Copy Results Feature ✅

#### 7.1 Copy Button
- [ ] "📋 Copy Results" button appears below summary
- [ ] Button is clickable
- [ ] Code block displays below button with formatted Markdown

**Expected**: Button clearly labeled for copying

---

#### 7.2 Copyable Text Format
- [ ] Text in code block is selectable
- [ ] Uses monospace font
- [ ] Format includes:
  - `## Pipeline Execution Summary` heading
  - Operation name
  - Status with emoji
  - Duration
  - Results list
- [ ] Can copy with Ctrl+C (Cmd+C on Mac)
- [ ] Paste test: Content pastes correctly into:
  - Email client
  - Slack message
  - Google Doc
  - Plain text editor

**Testing Method**:
1. Select all text in code block
2. Copy (Ctrl+C)
3. Paste into external application
4. Verify formatting is preserved

**Expected**: Clean Markdown that pastes well into communication tools

---

### 8. Data Exploration Interface ✅

#### 8.1 Table List Section
- [ ] "📊 Explore Results" section appears after pipeline completes
- [ ] Section is expandable/collapsible
- [ ] Table dropdown (selectbox) displays
- [ ] Dropdown populated with table names from MotherDuck
- [ ] Table names sorted alphabetically

**Expected**: Clean list of available tables for exploration

---

#### 8.2 Table Preview
- [ ] "Preview Table" checkbox/expander appears
- [ ] When checked, shows first 100 rows of selected table
- [ ] Uses `st.dataframe()` for display
- [ ] Dataframe is scrollable horizontally and vertically
- [ ] Column names are visible
- [ ] Data loads within 2-3 seconds

**Expected**: Quick preview of table contents without leaving page

---

#### 8.3 PyGWalker Integration
- [ ] "🔍 Open Interactive Explorer" button appears
- [ ] Button is below table selector
- [ ] Clicking button loads PyGWalker interface
- [ ] PyGWalker panel displays selected table data
- [ ] Can create charts (drag & drop interface works)
- [ ] Can apply filters
- [ ] Can perform aggregations

**Testing Method**:
1. Select a table (e.g., "job_cards")
2. Click "Open Interactive Explorer"
3. Try creating a simple bar chart
4. Apply a filter
5. Verify data updates correctly

**Expected**: Full PyGWalker functionality embedded in page

---

### 9. Error Handling Display ✅

#### 9.1 API Connection Errors
**Simulate**: Temporarily invalidate Trello API credentials in secrets.toml

- [ ] Error message displays with ❌ red marker
- [ ] Error text explains which API failed
- [ ] Error appears in log panel with red color
- [ ] Pipeline continues or stops gracefully (based on error type)
- [ ] Error traceback can be copied

**Expected**: Clear error identification without application crash

---

#### 9.2 MotherDuck Connection Errors
**Simulate**: Invalid MotherDuck token

- [ ] Connection status shows ❌ at page load
- [ ] "Run Full Pipeline" button is disabled
- [ ] Warning message explains connection issue
- [ ] Retry button allows re-checking connection

**Expected**: Graceful degradation with clear user guidance

---

#### 9.3 Error Details Copyable
- [ ] Error traceback appears in expandable section
- [ ] Traceback text is selectable
- [ ] Can copy full error for troubleshooting
- [ ] Error includes:
  - Error type
  - Error message
  - Full stack trace
  - Timestamp

**Expected**: Developers can copy error details for debugging

---

### 10. Responsive Design ✅

#### 10.1 Desktop View (1920x1080)
- [ ] Two columns display side-by-side
- [ ] Control panel width: ~33% (approx 640px)
- [ ] Feedback panel width: ~67% (approx 1280px)
- [ ] No horizontal scrolling required
- [ ] All text readable without zooming
- [ ] Buttons and inputs appropriately sized

**Expected**: Optimal layout for desktop use

---

#### 10.2 Tablet View (768x1024)
- [ ] Columns remain functional (may stack or resize)
- [ ] Button remains clickable
- [ ] Log messages readable
- [ ] Horizontal scrolling minimal or absent
- [ ] Touch targets large enough (buttons > 44px)

**Testing Method**:
1. Open browser DevTools (F12)
2. Toggle device toolbar
3. Select iPad (768x1024)
4. Verify layout

**Expected**: Usable interface on tablet devices

---

#### 10.3 Small Desktop (1366x768)
- [ ] Layout remains functional
- [ ] No content cut off
- [ ] Scrolling works correctly
- [ ] Two-column layout maintained

**Expected**: Works on smaller laptop screens

---

### 11. Session State Persistence ✅

#### 11.1 Log History
- [ ] Previous execution logs remain visible
- [ ] Can scroll back through log history
- [ ] History clears when new pipeline starts
- [ ] History persists across page interactions (button clicks)

**Expected**: Don't lose context during current session

---

#### 11.2 Operation History
- [ ] Past execution results stored (up to 20)
- [ ] Can view history in expandable section (if implemented)
- [ ] History survives page reruns within same session

**Expected**: Maintain execution context

---

### 12. Concurrent Execution Prevention ✅

#### 12.1 Single Execution Lock
- [ ] Click "Run Full Pipeline" once
- [ ] Try clicking button again while running
- [ ] Button becomes disabled
- [ ] Warning message appears if attempt made
- [ ] Lock releases when pipeline completes

**Expected**: Cannot start two pipelines simultaneously

---

### 13. Performance and Timing ✅

#### 13.1 Page Load Speed
- [ ] Page loads within 1-2 seconds
- [ ] Connection check completes quickly (<3 seconds)
- [ ] No blocking operations during initial load

**Expected**: Responsive page load

---

#### 13.2 Pipeline Execution
- [ ] Full pipeline completes within expected time (2-5 minutes)
- [ ] UI remains responsive during execution
- [ ] Can scroll logs while pipeline runs
- [ ] No browser tab freeze/hang

**Expected**: Long-running operation doesn't block UI

---

#### 13.3 Data Loading
- [ ] Table list loads quickly (<2 seconds)
- [ ] Table preview (100 rows) loads quickly (<3 seconds)
- [ ] PyGWalker loads within 5 seconds

**Expected**: Fast data access after pipeline completion

---

## Test Summary Checklist

After completing all tests above, verify:

- [ ] All visual elements render correctly
- [ ] All interactive elements (buttons, dropdowns) work
- [ ] Color coding displays properly (blue, green, yellow, red)
- [ ] Layout responsive at desktop and tablet sizes
- [ ] No console errors in browser DevTools
- [ ] Error handling graceful (no crashes)
- [ ] Copy/paste functionality works
- [ ] Session state persists correctly
- [ ] Performance acceptable (no lag or freezing)

---

## Browser Compatibility

Test in at least **two** of these browsers:

- [ ] Chrome/Chromium (v120+)
- [ ] Firefox (v120+)
- [ ] Safari (v17+)
- [ ] Edge (v120+)

**Expected**: Consistent behavior across modern browsers

---

## Known Issues / Limitations

Document any issues found during testing:

1. **Issue**: [Description]
   - **Severity**: Critical / High / Medium / Low
   - **Steps to Reproduce**: [Steps]
   - **Expected**: [Expected behavior]
   - **Actual**: [Actual behavior]
   - **Workaround**: [If any]

2. _(Add more as needed)_

---

## Testing Completion

**Tested By**: _________________
**Date**: _________________
**Browser(s)**: _________________
**Screen Resolution(s)**: _________________

**Overall Result**: ✅ Pass / ❌ Fail / ⚠️ Pass with Issues

**Notes**:
_[Add any additional observations or recommendations]_

---

## Next Steps After Testing

1. **If all tests pass**: Mark T016 as complete, proceed to T018 (final validation)
2. **If issues found**: Document in "Known Issues" section, create bug report, fix critical issues
3. **After fixes**: Re-run failed test scenarios to verify resolution

---

## References

- **Spec**: `specs/002-fix-and-improve/spec.md` (FR-030, FR-031, FR-032)
- **Quickstart**: `specs/002-fix-and-improve/quickstart.md` (Testing Checklist)
- **Implementation**: `enviroflow_app/pages/6_🚚_Data_Loading_ELT.py`
