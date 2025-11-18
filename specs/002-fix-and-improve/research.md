# Research: Data Pipeline GUI Controller

## Overview
This document captures design decisions and research findings for implementing a Streamlit GUI wrapper around the existing CLI data pipeline.

## Key Design Decisions

### 1. UI Architecture Pattern
**Decision**: Two-column layout with control panel (left) and feedback/results panel (right)

**Rationale**:
- Matches existing patterns in Data Explorer (7_🔮_Data_Explorer.py) and Subcontract Generator (3_📝_Subcontract_Generator.py)
- User familiarity - users already understand this layout
- Efficient space utilization for displaying logs and results
- Left-to-right workflow feels natural (select operation → view results)

**Alternatives Considered**:
- Tabbed interface: Rejected - hides feedback while selecting operations
- Single column: Rejected - poor space utilization for side-by-side viewing
- Modal dialogs: Rejected - interrupts workflow and hides context

### 2. Real-Time Feedback Mechanism
**Decision**: Use Streamlit's `st.empty()` containers with streaming log updates

**Rationale**:
- Native Streamlit pattern for dynamic content updates
- Can update UI in real-time as pipeline executes
- No additional dependencies (no WebSockets or custom streaming)
- Already proven pattern in existing codebase

**Alternatives Considered**:
- `st.spinner()`: Rejected - blocks UI, no granular feedback
- Custom WebSocket: Rejected - adds complexity, violates simplicity principle
- Polling: Rejected - inefficient, delays feedback

**Implementation Pattern**:
```python
log_container = st.empty()
with log_container.container():
    for log_message in pipeline_execution():
        st.markdown(f":{color_icon}: {timestamp} {message}")
```

### 3. Pipeline Operation Execution
**Decision**: Direct function calls to `enviroflow_app/cli/operations/*` modules

**Rationale**:
- CLI operations are already designed to be imported and called as functions
- No need for subprocess execution or CLI command wrapping
- Same code path as CLI ensures consistent behavior
- Simplest possible implementation

**Alternatives Considered**:
- Subprocess calls to CLI: Rejected - adds complexity, harder to capture output
- Duplicate logic: Rejected - violates DRY, maintenance burden
- REST API wrapper: Rejected - massive over-engineering

**Implementation Pattern**:
```python
from enviroflow_app.cli.operations import extraction_ops
result = extraction_ops.extract_trello_data()
```

### 4. Execution State Management
**Decision**: Use Streamlit session state with execution tracking keys

**Rationale**:
- Native Streamlit pattern for cross-rerun state
- Already established pattern in codebase (`pre.py` helpers)
- Simple boolean flags and message lists
- Survives page reruns automatically

**Session State Schema**:
```python
ss.pipeline_running: bool = False  # Prevent concurrent executions
ss.current_operation: str | None   # Name of running operation
ss.execution_log: list[dict]       # Log messages with timestamp, level, message
ss.last_results: dict | None       # Most recent execution results
ss.operation_history: list[dict]   # Session execution history
```

**Alternatives Considered**:
- Database persistence: Rejected - overkill for session-only data
- File-based state: Rejected - adds I/O complexity
- Global variables: Rejected - unreliable in Streamlit's execution model

### 5. Log Message Categorization
**Decision**: Use emoji icons and Streamlit color helpers for visual categorization

**Rationale**:
- Matches existing codebase style (emoji prefixes for pages)
- No custom CSS required for basic functionality
- Accessible and clear visual distinction
- Fast user scanning for errors/warnings

**Color Scheme**:
```python
INFO:    🔵 st.info() - blue
SUCCESS: ✅ st.success() - green
WARNING: ⚠️  st.warning() - yellow
ERROR:   ❌ st.error() - red
```

**Alternatives Considered**:
- Rich console output: Rejected - doesn't work well in Streamlit
- Custom CSS classes: Rejected - harder to maintain, accessibility concerns
- Plain text: Rejected - poor user experience for scanning

### 6. Copyable Results Format
**Decision**: Formatted Markdown text with `st.code()` for easy copying

**Rationale**:
- Native browser text selection and copy
- Markdown format is human-readable and paste-friendly
- Can include structured data (tables, lists) in copy
- Works in email, Slack, documents without modification

**Format Example**:
```markdown
## Pipeline Execution Summary
Operation: Extract Trello Data
Status: ✅ Success
Duration: 23.4 seconds
Records Processed: 247 job cards

### Results
- Extracted: 247 job cards
- Saved to: MotherDuck table 'job_cards'
- Validation: ✅ All records valid
```

**Alternatives Considered**:
- JSON format: Rejected - not human-readable
- CSV export: Rejected - doesn't capture nested information well
- Custom copy button: Rejected - adds complexity, browser native is simpler

### 7. Data Table Exploration
**Decision**: Reuse PyGWalker integration pattern from Data Explorer

**Rationale**:
- Already proven in Data Explorer page
- Users are familiar with the interface
- Provides rich exploratory capabilities (charts, filters, aggregations)
- No additional development work needed

**Implementation**: After pipeline completion, show "Explore Results" button that loads data into PyGWalker viewer following the exact pattern in `7_🔮_Data_Explorer.py` lines 331-380.

**Alternatives Considered**:
- st.dataframe only: Rejected - limited interactivity
- Custom visualization: Rejected - reinventing the wheel
- Link to Data Explorer: Rejected - interrupts workflow

### 8. Error Handling Strategy
**Decision**: Graceful degradation with clear user messaging and fallback options

**Rationale**:
- External APIs (Trello, Float, Google Sheets) can fail
- MotherDuck connection can be interrupted
- Users need clear next steps, not cryptic errors

**Error Handling Tiers**:
1. **Operation-level**: Try/except around each operation, log error, continue to next operation
2. **Connection-level**: Fallback to local files if MotherDuck unavailable (existing CLI pattern)
3. **API-level**: Show which specific API failed, suggest retry or skip
4. **User-level**: Display actionable error message with copy functionality for support

**Implementation Pattern**:
```python
try:
    result = extraction_ops.extract_trello_data()
    log_success(f"Extracted {len(result)} job cards")
except TrelloAPIError as e:
    log_error(f"Trello API failed: {e}")
    st.error("Could not connect to Trello. Check your API credentials.")
    if st.button("Retry"):
        st.rerun()
except Exception as e:
    log_error(f"Unexpected error: {e}")
    st.error(f"Operation failed: {e}")
    with st.expander("Error Details (click to copy)"):
        st.code(traceback.format_exc())
```

### 9. Concurrency Control
**Decision**: Simple session-level locking with `ss.pipeline_running` flag

**Rationale**:
- Prevents user confusion from overlapping operations
- Protects data integrity (avoid race conditions on table writes)
- Simple implementation - just a boolean check
- Good enough for small team usage

**Limitations Accepted**:
- Not true multi-user locking (different users can run simultaneously)
- Single session can't run multiple operations in parallel
- Acceptable trade-off: Small team, infrequent usage, operations complete in minutes

**Future Enhancement** (out of scope): If multi-user conflicts become an issue, implement database-level locks or job queue.

**Alternatives Considered**:
- Redis-based distributed lock: Rejected - over-engineering
- Database locks: Rejected - adds complexity
- Queue system: Rejected - not needed for current scale

### 10. Progress Indication
**Decision**: Indeterminate spinner + live log messages (no progress bar)

**Rationale**:
- Pipeline operations don't report percentage completion
- Log messages provide more informative feedback than a progress bar
- Spinner indicates "system is working"
- Matches expectations for data pipeline operations

**Implementation**:
```python
with st.spinner(f"Running {operation_name}..."):
    for step_result in execute_operation():
        append_log_message(step_result)
st.success(f"{operation_name} completed!")
```

**Alternatives Considered**:
- Progress bar with estimated time: Rejected - operations have variable duration
- Percentage completion: Rejected - would require instrumenting all operations
- No indicator: Rejected - poor UX, users think app is frozen

### 11. UI Visual Verification and Testing
**Decision**: Manual browser testing for all UI changes with visual inspection

**Rationale**:
- Streamlit apps are inherently visual - automated tests can't catch layout issues
- Two-column layout needs visual verification to ensure proper rendering
- Color-coded log messages must be verified for accessibility and clarity
- Interactive elements (buttons, dropdowns) need click-testing
- Responsive behavior across screen sizes requires manual testing

**Testing Approach**:
```python
# After implementing UI changes:
1. Launch Streamlit app: streamlit run enviroflow_app/🏠_Home.py
2. Navigate to Data Loading page
3. Visual checks:
   - Two-column layout renders correctly
   - Control panel (left) shows all operation buttons
   - Feedback panel (right) has adequate space
   - Colors display correctly (blue info, green success, yellow warning, red error)
   - Text is readable and properly sized
   - Buttons are clickable and respond to hover
4. Test responsive behavior:
   - Resize browser window to tablet width (~768px)
   - Verify columns adapt or stack appropriately
   - Check that content remains accessible
5. Test interactions:
   - Click operation buttons - verify state changes
   - Check spinners appear during execution
   - Verify log messages scroll automatically
   - Test "Copy Results" button functionality
```

**Why This Matters**:
- Streamlit's rendering can behave differently than expected from code alone
- CSS and layout issues only visible in browser
- User experience heavily dependent on visual presentation
- Catches issues before users encounter them

**Testing Checklist** (for each UI change):
- [ ] Layout renders as expected in desktop view (1920x1080)
- [ ] Layout adapts correctly in tablet view (768x1024)
- [ ] All interactive elements are clickable
- [ ] Color coding is clear and accessible
- [ ] Text is readable and properly sized
- [ ] No visual glitches or overlapping elements
- [ ] Feedback panel updates in real-time
- [ ] Page loads without console errors (F12 developer tools)

**Alternatives Considered**:
- Visual regression testing tools (Percy, Chromatic): Rejected - overkill for single page, adds complexity
- Automated browser testing (Selenium): Rejected - brittle for Streamlit, maintenance burden
- Code-only testing: Rejected - insufficient for visual UI validation

## Technology Stack Verification

**Core Dependencies** (all already in project):
- ✅ Streamlit 1.x - UI framework
- ✅ Polars 1.32+ - Data processing
- ✅ PyGWalker - Data exploration
- ✅ Rich Console - Used by CLI operations for formatting

**No New Dependencies Required**

## Performance Considerations

**Expected Operation Durations** (from existing CLI usage):
- Extract Trello: 10-30 seconds
- Extract Float: 15-45 seconds
- Extract Xero Costs (Google Sheets): 30-90 seconds
- Transform operations: 5-20 seconds each
- Full pipeline: 2-5 minutes

**Streamlit Timeout Handling**:
- Default Streamlit script timeout: 300 seconds (5 minutes)
- Full pipeline fits within timeout
- Individual operations well under limit
- No custom timeout configuration needed

**Memory Considerations**:
- Largest dataset: 30,996 sales records (from spec research)
- Polars DataFrames are memory-efficient
- Expected peak memory: <500MB
- Well within typical deployment limits

## Security & Credentials

**Existing Pattern** (reuse, no changes):
```python
# .streamlit/secrets.toml (not in git)
[motherduck]
token = "..."
db = "enviroflow"

[trello]
api_key = "..."
api_token = "..."

[float]
api_key = "..."

# Access in code
import streamlit as st
token = st.secrets["motherduck"]["token"]
```

**No Security Changes Needed** - feature uses existing credential infrastructure.

## Integration Points

**Existing Infrastructure to Reuse**:
1. `enviroflow_app/st_components/pre.py` - Session state initialization
2. `enviroflow_app/elt/motherduck/md.py` - Database connection
3. `enviroflow_app/cli/operations/*` - All pipeline operations
4. `enviroflow_app/cli/config.py` - Pipeline configuration objects
5. `enviroflow_app/cli/dag/pipeline.py` - Full pipeline orchestration

**No New Integration Layers Needed** - feature composition of existing components.

## Open Questions Resolved

Q: How to handle long-running operations in Streamlit's synchronous model?
A: Streamlit's default execution model works fine. Operations complete within timeout. No async needed.

Q: How to stream log output in real-time?
A: Use `st.empty()` containers updated in a loop. Native Streamlit pattern.

Q: Should we create a new abstraction layer between GUI and CLI?
A: No. Direct function calls. Simplicity principle.

Q: How to test GUI components?
A: Integration tests that import the page functions and test with mock session state. Existing pattern in codebase.

Q: What if user closes browser during operation?
A: Operation continues server-side (Streamlit session persists). User sees status on return. Acceptable behavior.

## Success Metrics

**How we'll know the implementation is successful**:
1. All 15+ CLI operations accessible via GUI buttons
2. Real-time log messages appear within 1 second of operation events
3. Users can copy results and paste into Slack/email readably
4. Zero new dependencies added to `pyproject.toml`
5. Page load time <3 seconds
6. Integration tests pass with >90% coverage
7. No modifications to `enviroflow_app/cli/` code required
8. User testing: Business user can run full pipeline without documentation
9. **Visual verification: All UI changes tested in browser with layout, colors, and interactions confirmed working across desktop and tablet viewports**

## References

**Code Patterns to Follow**:
- `enviroflow_app/pages/7_🔮_Data_Explorer.py` - Two-column layout, data exploration
- `enviroflow_app/pages/3_📝_Subcontract_Generator.py` - Form submission, session state usage
- `enviroflow_app/st_components/pre.py` - Session initialization patterns
- `enviroflow_app/cli/operations/extraction_ops.py` - Operation function signatures

**Documentation**:
- Streamlit docs: Session state, empty containers, layout
- Existing project docs: `docs/dev_notes/03_Development_Patterns.md`
- Constitution: `.specify/memory/constitution.md`

---

**Research Complete**: All design decisions made. Ready for Phase 1 (Data Model & Contracts).
