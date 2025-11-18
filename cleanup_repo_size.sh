#!/bin/bash
set -e

echo "🧹 Repository Size Cleanup Script"
echo "=================================="
echo ""
echo "Current .git size:"
du -sh .git
echo ""

# Backup reminder
echo "⚠️  WARNING: This will rewrite git history!"
echo "Make sure you have a backup of your repository before proceeding."
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Remove large files from history using git-filter-repo
echo ""
echo "Step 1: Installing git-filter-repo if needed..."
if ! command -v git-filter-repo &> /dev/null; then
    echo "Installing git-filter-repo..."
    pip install git-filter-repo
fi

# Step 2: Create list of files to remove
echo ""
echo "Step 2: Creating list of large files to remove from history..."
cat > /tmp/files_to_remove.txt << 'EOF'
logs/full_log
Closed_Jobs.json
closed_jobs.json
invoices.json
Static/chromedriver
Data/xero_data/quotes_df.csv
Data/cli_pipeline_data/raw_json/trello_old_completed_jobs.json
Data/cli_pipeline_data/raw_json/trello_completed_jobs.json
Data/cli_pipeline_data/raw_json/xero_quotes.json
EOF

echo "Files to be removed from history:"
cat /tmp/files_to_remove.txt
echo ""

# Step 3: Remove files from history
echo "Step 3: Removing files from git history..."
git filter-repo --invert-paths --paths-from-file /tmp/files_to_remove.txt --force

# Step 4: Run garbage collection
echo ""
echo "Step 4: Running aggressive garbage collection..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Step 5: Show new size
echo ""
echo "✅ Cleanup complete!"
echo "New .git size:"
du -sh .git
echo ""
echo "⚠️  Next steps:"
echo "1. Review your repository to ensure everything looks correct"
echo "2. Force push to GitHub: git push origin --force --all"
echo "3. Force push tags: git push origin --force --tags"
echo "4. Inform collaborators to re-clone the repository"
echo ""
echo "Note: GitHub may still reject the push if the pack size is too large."
echo "In that case, consider Option 2: creating a fresh repository."
