# Streamlit Cloud Deployment Performance

## Current Status (Oct 3, 2025)

**Repository Size:**
- `.git` directory: 3.0 GB
- Working tree (Data ignored): ~50 MB
- Total clone size: ~3.0 GB

**Known Issues:**
- Large git history from legacy data files (logs, JSON files)
- Cannot prune history due to GitHub limitations on large repos
- Streamlit Cloud does not support shallow clones

## Deployment Metrics

### Baseline (to be filled in)
- **First deployment time:** ___ minutes
- **Subsequent deployments:** ___ seconds/minutes
- **Build cache hit rate:** ___

### Optimization Actions Taken
1. ✅ Data folder already in `.gitignore`
2. ✅ App reads from MotherDuck (no local data dependency)
3. ⏳ Monitor deployment times

## If Deployment Becomes Too Slow

### Option 1: Fresh Repository (Nuclear Option)
Only if deployment times exceed 10 minutes consistently:
- Create new repo with current state only
- Archive old repo for history
- Update Streamlit Cloud deployment URL
- **Scripts ready:** `create_fresh_repo.sh` (already exists)

### Option 2: External Data Storage
Already implemented! App uses MotherDuck.

### Option 3: Docker Deployment
If Streamlit Cloud becomes problematic:
- Deploy via Docker container
- Use shallow clone in Dockerfile
- Host on Cloud Run, Railway, or Fly.io

## Decision Point

**Don't act unless:**
- Deployment takes >10 minutes
- GitHub repo hits size limits (10GB)
- Streamlit Cloud deployment fails

**Current verdict:** Monitor but don't change. The repo works fine as-is.
