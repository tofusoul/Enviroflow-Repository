# Repository Size Reduction Guide

**Date**: October 3, 2025
**Problem**: Repository .git directory is 3.0GB, causing deployment and clone issues
**Root Cause**: Large files committed to git history (logs, JSON data files, binaries)

## Current Situation Analysis

### Size Breakdown
- **.git directory**: 3.0GB
- **Working directory** (without .git): 2.0GB
- **Data/ folder**: 156MB (already gitignored, not the problem)

### Largest Files in Git History
```
104MB - logs/full_log
57MB  - logs/full_log (another version)
46MB  - Closed_Jobs.json / closed_jobs.json
28MB  - Data/cli_pipeline_data/raw_json/xero_quotes.json
28MB  - Data/cli_pipeline_data/raw_json/trello_completed_jobs.json
27MB  - invoices.json
17MB  - Data/cli_pipeline_data/raw_json/trello_old_completed_jobs.json
15MB  - Static/chromedriver
13MB+ - Data/xero_data/quotes_df.csv (multiple versions)
```

### Why Streamlit Cloud is Affected
- **Streamlit Cloud always performs full clones** (no shallow clone option available)
- Every deployment clones the entire git history
- 3GB repository significantly slows down deployment
- May hit Streamlit Cloud size limits

## Solution Options

### Option 1: Create Fresh Repository (RECOMMENDED) ⭐

**Pros:**
- ✅ Clean, guaranteed to work
- ✅ No GitHub push size limitations
- ✅ Preserves old repository for historical reference
- ✅ Fresh start with proper .gitignore from day 1
- ✅ Simple and fast process

**Cons:**
- ❌ Loses commit history (but old repo can be archived)
- ❌ Need to update Streamlit Cloud deployment settings
- ❌ Collaborators need to clone new repo

**Steps:**

1. **Verify current .gitignore is comprehensive**
   ```bash
   # Already includes:
   # - Data/ (all data files)
   # - logs/*.log, logs/*.csv, logs/full_log
   # - *.db, *.sqlite files
   # - Large JSON files (invoices.json, etc.)
   # - Static/chromedriver
   ```

2. **Create new repository on GitHub**
   - Name: `Enviroflow_App_v2` (or keep same name if you delete old one)
   - Initialize as empty (no README, no .gitignore)

3. **Prepare current repository**
   ```bash
   # Ensure all large files are in .gitignore
   git rm --cached -r Data/ 2>/dev/null || true
   git rm --cached logs/full_log 2>/dev/null || true
   git rm --cached Closed_Jobs.json closed_jobs.json invoices.json 2>/dev/null || true
   git rm --cached Static/chromedriver 2>/dev/null || true

   # Commit the removal
   git add .gitignore
   git commit -m "Remove large files from tracking before migration"
   ```

4. **Create fresh repo with current state**
   ```bash
   # Save current branch name
   current_branch=$(git branch --show-current)

   # Create a new orphan branch (no history)
   git checkout --orphan fresh-start

   # Add all files (respecting .gitignore)
   git add .

   # Create initial commit
   git commit -m "Initial commit: Clean repository migration

   - Migrated from legacy repository with 3GB git history
   - Removed large historical data files
   - All data files now properly gitignored
   - See archived repository for full history"

   # Delete old branch and rename
   git branch -D $current_branch
   git branch -m $current_branch
   ```

5. **Push to new repository**
   ```bash
   # Add new remote (or update existing)
   git remote remove origin
   git remote add origin https://github.com/tofusoul/Enviroflow_App_v2.git

   # Push fresh repository
   git push -u origin main --force
   ```

6. **Update Streamlit Cloud**
   - Go to Streamlit Cloud dashboard
   - Delete old app deployment
   - Create new deployment pointing to new repository
   - Re-add secrets in Streamlit Cloud UI

7. **Archive old repository**
   - Go to old GitHub repository settings
   - Scroll to "Danger Zone"
   - Click "Archive this repository"
   - Add note: "Archived - Migrated to Enviroflow_App_v2 due to repository size issues"

**Expected Result:**
- New repository: ~100-200MB (without git history bloat)
- Fast Streamlit Cloud deployments
- Clean git history moving forward

---

### Option 2: Clean Git History (COMPLEX, MAY FAIL) ⚠️

**Pros:**
- ✅ Keeps same repository URL
- ✅ Preserves recent commit history

**Cons:**
- ❌ Complex process, easy to make mistakes
- ❌ GitHub may reject force push due to pack size
- ❌ All collaborators must re-clone
- ❌ Can corrupt repository if done wrong
- ❌ May not achieve sufficient size reduction

**Steps:**

1. **Create backup**
   ```bash
   # Clone to backup location
   cd /tmp
   git clone --mirror https://github.com/tofusoul/Enviroflow_App.git backup-repo
   cd -
   ```

2. **Install git-filter-repo**
   ```bash
   pip install git-filter-repo
   ```

3. **Run cleanup script**
   ```bash
   chmod +x cleanup_repo_size.sh
   ./cleanup_repo_size.sh
   ```

4. **Test locally**
   ```bash
   # Check repository integrity
   git fsck --full

   # Verify app still works
   streamlit run enviroflow_app/🏠_Home.py
   ```

5. **Force push (may fail)**
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```

   **If push fails with "pack too large" error:**
   - GitHub has limits on push size
   - You MUST use Option 1 (fresh repository) instead

6. **Notify collaborators**
   - Everyone must delete their local clone
   - Everyone must re-clone: `git clone https://github.com/tofusoul/Enviroflow_App.git`

---

## Recommended Approach: OPTION 1

**Why Option 1 is better:**

1. **Guaranteed to work** - No GitHub push size limits
2. **Faster** - Takes 10 minutes instead of hours of troubleshooting
3. **Cleaner** - Fresh git history from this point forward
4. **Safer** - Old repository preserved as archive
5. **Simpler** - Fewer steps, less room for error

**What you'll lose:**
- Commit history (but you can reference old repo if needed)
- GitHub issues/PRs (if any - can be migrated if needed)

**What you'll keep:**
- All current code and configuration
- All current documentation
- .gitignore properly configured
- Clean, fast repository

## Prevention: Best Practices for Future

### 1. Update .gitignore (Already Done ✅)
Current .gitignore already includes:
- `Data/` - All data files
- `logs/*.log`, `logs/*.csv`, `logs/full_log`
- `*.db`, `*.sqlite*` files
- Large JSON files pattern

### 2. Pre-commit Hook (Optional)
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Prevent committing large files
MAX_SIZE=10485760  # 10MB in bytes

large_files=$(git diff --cached --name-only | xargs -I {} du -b {} 2>/dev/null | awk -v max=$MAX_SIZE '$1 > max {print $2}')

if [ -n "$large_files" ]; then
    echo "❌ Error: Attempting to commit large files:"
    echo "$large_files"
    echo ""
    echo "Please add these to .gitignore or use Git LFS"
    exit 1
fi
```

### 3. Use Git LFS for Necessary Large Files
If you need to version control large files:
```bash
# Install Git LFS
sudo apt-get install git-lfs  # or: brew install git-lfs
git lfs install

# Track file types
git lfs track "*.parquet"
git lfs track "*.db"

# Commit .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS"
```

### 4. Store Data Externally
- Use **MotherDuck** for production data (already planned in migration)
- Use **cloud storage** (S3, GCS) for large datasets
- Keep only small sample/test data in repository

### 5. Regular Cleanup Checks
```bash
# Check repository size monthly
du -sh .git

# Find large files before they accumulate
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sed -n 's/^blob //p' | \
  sort -nk2 | \
  tail -10
```

## Troubleshooting

### After Fresh Repository Creation

**Problem**: Streamlit Cloud still slow to deploy
- **Cause**: May have cached old repository
- **Solution**: Delete and recreate app deployment in Streamlit Cloud

**Problem**: Secrets missing
- **Cause**: Secrets don't transfer automatically
- **Solution**: Re-add secrets in Streamlit Cloud UI under app settings

### If Git History Cleanup Fails

**Problem**: `git push` fails with "pack too large"
- **Cause**: GitHub has push size limits (~2GB)
- **Solution**: Must use Option 1 (fresh repository)

**Problem**: Repository corrupted after filter-repo
- **Cause**: Interrupted process or filter errors
- **Solution**: Delete local repo, restore from backup:
  ```bash
  cd ..
  rm -rf Enviroflow_App
  git clone /tmp/backup-repo Enviroflow_App
  cd Enviroflow_App
  ```

## Next Steps

1. **Decision**: Choose Option 1 (recommended) or Option 2
2. **Backup**: Create backup copy of current repository
3. **Execute**: Follow steps for chosen option
4. **Verify**: Test app locally after migration
5. **Deploy**: Update Streamlit Cloud configuration
6. **Document**: Update AGENTS.md and .github/copilot-instructions.md with new repo URL if changed

## References

- [Git Filter-Repo Documentation](https://github.com/newren/git-filter-repo)
- [GitHub Repository Size Limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
- [Streamlit Cloud Deployment Docs](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [Git LFS Documentation](https://git-lfs.github.com/)
