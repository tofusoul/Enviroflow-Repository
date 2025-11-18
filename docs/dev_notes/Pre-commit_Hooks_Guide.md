# Pre-commit Hooks Guide

This repository uses [pre-commit](https://pre-commit.com/) to enforce code quality and security standards.

## What Are Pre-commit Hooks?

Pre-commit hooks automatically run checks **before** you commit code, catching issues early:
- 🔐 Secrets and credentials detection
- 🚫 Prevents Data folder commits
- ✨ Code formatting with Ruff
- 🧹 File cleanup (trailing whitespace, EOF)
- 📏 Large file detection

## Installation

Pre-commit hooks are already configured. To activate them:

```bash
# Install pre-commit package (already in requirements)
poetry install

# Install git hooks
pre-commit install
```

**Done!** Hooks will now run automatically on every `git commit`.

## What Happens When You Commit

When you run `git commit`, pre-commit automatically:

1. **Checks for secrets** - Blocks commits with API keys, tokens, passwords
2. **Blocks Data folder** - Prevents accidental Data/ commits
3. **Detects private keys** - Stops SSH/RSA key commits
4. **Formats Python code** - Runs Ruff auto-formatting
5. **Fixes file issues** - Removes trailing whitespace, fixes EOFs
6. **Checks YAML** - Validates YAML file syntax
7. **Blocks large files** - Prevents files >1MB

If all checks pass ✅ - Your commit succeeds!
If any check fails ❌ - Commit blocked, issues explained

## Common Scenarios

### ✅ Normal Commit (All Checks Pass)

```bash
git add myfile.py
git commit -m "Add new feature"
# All hooks run, all pass
# Commit succeeds
```

### ❌ Secret Detected

```bash
git add config.py  # Contains API key
git commit -m "Update config"
# ❌ Detect secrets...Failed
# ERROR: Secret detected in config.py
# Commit blocked
```

**Fix**: Remove secrets, use environment variables instead.

### ⚠️ Auto-fixed Issues

```bash
git add myfile.py  # Has trailing whitespace
git commit -m "Update file"
# ⚠️ trim trailing whitespace...Failed (auto-fixed)
# File modified, try commit again
```

**Fix**: Just commit again - pre-commit already fixed the issue!

### 🚫 Data Folder Block

```bash
git add Data/my_data.csv
git commit -m "Add data"
# ❌ Block Data folder commits...Failed
# ERROR: Cannot commit files in Data/ folder
# Commit blocked
```

**Fix**: Data belongs in the separate `Enviroflow_Data` repository.

## Manual Hook Execution

Run all hooks on all files without committing:

```bash
# Check all files
pre-commit run --all-files

# Check specific hook
pre-commit run detect-secrets --all-files

# Check specific files
pre-commit run --files myfile.py otherfile.py
```

## Skipping Hooks (Emergency Only)

**⚠️ Not recommended** - Only use in true emergencies:

```bash
git commit --no-verify -m "Emergency fix"
```

This bypasses ALL hooks. Use with extreme caution.

## Hook Configuration

Hooks are configured in `.pre-commit-config.yaml`. To update:

```bash
# Update hook versions
pre-commit autoupdate

# Migrate to latest config format
pre-commit migrate-config
```

## Troubleshooting

### Hooks Not Running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Test installation
pre-commit run --all-files
```

### False Positive Secrets

If detect-secrets flags something that isn't a secret:

```bash
# Update baseline to exclude it
detect-secrets scan --update .secrets.baseline

# Commit the updated baseline
git add .secrets.baseline
git commit -m "Update secrets baseline"
```

### Hook Taking Too Long

Hooks only run on **staged files**, not the entire repo.
If a specific hook is slow, you can disable it in `.pre-commit-config.yaml`.

## Hooks Included

| Hook | Purpose | Auto-fix |
|------|---------|----------|
| `trailing-whitespace` | Remove trailing spaces | ✅ Yes |
| `end-of-file-fixer` | Ensure files end with newline | ✅ Yes |
| `check-yaml` | Validate YAML syntax | ❌ No |
| `check-added-large-files` | Block files >1MB | ❌ No |
| `check-merge-conflict` | Detect merge markers | ❌ No |
| `detect-private-key` | Block SSH/RSA keys | ❌ No |
| `detect-secrets` | Block API keys/tokens | ❌ No |
| `ruff` | Python linting | ✅ Yes (with --fix) |
| `ruff-format` | Python formatting | ✅ Yes |
| `block-data-folder` | Block Data/ commits | ❌ No |

## Best Practices

1. **Run hooks locally** before pushing to catch issues early
2. **Don't skip hooks** unless absolutely necessary
3. **Keep hooks updated** with `pre-commit autoupdate`
4. **Use environment variables** for secrets instead of files
5. **Commit secret baselines** when false positives are verified

## Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Detect Secrets](https://github.com/Yelp/detect-secrets)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- Repository cleanup: `docs/dev_notes/Repository_Cleanup_Summary.md`

## Questions?

If you encounter issues or have questions about pre-commit hooks, check:
1. This guide
2. `.pre-commit-config.yaml` - Hook configuration
3. Repository cleanup summary in `docs/dev_notes/`
