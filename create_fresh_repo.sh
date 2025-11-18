#!/bin/bash
set -e

echo "🚀 Fresh Repository Migration Script"
echo "====================================="
echo ""
echo "This script will create a fresh git repository with no history,"
echo "keeping only the current state of your code."
echo ""
echo "Current .git size: $(du -sh .git | cut -f1)"
echo ""

# Safety checks
if [ ! -f ".gitignore" ]; then
    echo "❌ Error: .gitignore not found. Are you in the repository root?"
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes."
    echo "Please commit or stash them before running this script."
    exit 1
fi

echo "⚠️  WARNING: This will:"
echo "  1. Create a new git repository with no history"
echo "  2. You'll need to force push to a new GitHub repository"
echo "  3. All collaborators will need to re-clone"
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Get current branch name
current_branch=$(git branch --show-current)
echo ""
echo "Current branch: $current_branch"

# Remove any large files that might still be tracked
echo ""
echo "Step 1: Ensuring large files are not tracked..."
git rm --cached -r Data/ 2>/dev/null || true
git rm --cached logs/full_log 2>/dev/null || true
git rm --cached Closed_Jobs.json closed_jobs.json invoices.json 2>/dev/null || true
git rm --cached Static/chromedriver 2>/dev/null || true

# Commit if there are changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Committing removal of large files..."
    git add .gitignore
    git commit -m "Remove large files from tracking before migration" || true
fi

# Create backup of remotes
echo ""
echo "Step 2: Saving remote URLs..."
git remote -v > /tmp/git_remotes_backup.txt
echo "Remote URLs saved to /tmp/git_remotes_backup.txt"
cat /tmp/git_remotes_backup.txt

# Create fresh orphan branch
echo ""
echo "Step 3: Creating fresh branch with no history..."
git checkout --orphan fresh-start

# Stage all files (respecting .gitignore)
echo ""
echo "Step 4: Staging current files..."
git add .

# Create initial commit
echo ""
echo "Step 5: Creating initial commit..."
git commit -m "Initial commit: Clean repository migration

- Migrated from legacy repository with 3GB git history
- Removed large historical data files from tracking
- All data files now properly gitignored
- See archived repository for full history

Migration date: $(date +%Y-%m-%d)
Previous branch: $current_branch"

# Delete old branches
echo ""
echo "Step 6: Cleaning up old branches..."
for branch in $(git branch | grep -v fresh-start | grep -v \*); do
    git branch -D "$branch" 2>/dev/null || true
done

# Rename branch to original name
git branch -m fresh-start "$current_branch"

# Remove old git objects
echo ""
echo "Step 7: Removing old git history..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Show new size
echo ""
echo "✅ Migration complete!"
echo ""
echo "New .git size: $(du -sh .git | cut -f1)"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Create a new repository on GitHub (or delete the old one if you want to keep the same name)"
echo ""
echo "2. Update remote URL:"
echo "   git remote remove origin"
echo "   git remote add origin https://github.com/tofusoul/NEW_REPO_NAME.git"
echo ""
echo "3. Push to new repository:"
echo "   git push -u origin $current_branch --force"
echo ""
echo "4. Update Streamlit Cloud:"
echo "   - Delete old app deployment"
echo "   - Create new deployment pointing to new repository"
echo "   - Re-add secrets in Streamlit Cloud UI"
echo ""
echo "5. Archive old repository on GitHub:"
echo "   - Go to old repository settings"
echo "   - Archive in 'Danger Zone' section"
echo ""
echo "Your original remote URLs (for reference):"
cat /tmp/git_remotes_backup.txt
echo ""
echo "🎉 You now have a clean, lightweight repository!"
