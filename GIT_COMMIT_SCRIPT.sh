#!/bin/bash
# Script to create branch, commit changes, and push to GitHub

echo "=========================================="
echo "Size Optimization Pipeline - Git Workflow"
echo "=========================================="
echo

# Create new branch
echo "Creating branch: size-optimization-pipeline"
git checkout -b size-optimization-pipeline

# Stage all changes
echo "Staging changes..."
git add size_optimization_pipeline.py
git add cleanup_non_size_files.py
git add archive_non_size_files/
git add requirements.txt
git add .gitignore
git add demo.py
git add replit.md
git add CREATE_PR_INSTRUCTIONS.md
git add GIT_COMMIT_SCRIPT.sh

# Show status
echo
echo "Files to be committed:"
git status --short

# Commit
echo
echo "Committing changes..."
git commit -m "Add size optimization pipeline and cleanup non-size files

- Created comprehensive size optimization pipeline combining static and LLM analysis
- Added filter for size-related recommendations only
- Track and save Dockerfiles at each optimization stage (original, static, LLM)
- Calculate and report potential size savings in KB/MB
- Moved non-size files (research papers, analysis data, utility scripts) to archive
- Updated project documentation and configuration
- Added demo script and improved .gitignore

This focuses the repository on Docker image size optimization specifically,
separating it from general security and performance analysis."

# Push to GitHub
echo
echo "Pushing to GitHub..."
git push -u origin size-optimization-pipeline

echo
echo "=========================================="
echo "✓ Branch created and pushed successfully!"
echo "=========================================="
echo
echo "Next steps:"
echo "1. Go to: https://github.com/onetrueheisenberg/cps-ci-cd-analysis"
echo "2. Click 'Pull requests' > 'New pull request'"
echo "3. Select base: main, compare: size-optimization-pipeline"
echo "4. Fill in PR details (see CREATE_PR_INSTRUCTIONS.md)"
echo "5. Click 'Create pull request'"
echo

# Print PR URL hint
echo "GitHub may also show a direct link to create the PR after push."
echo "Look for: 'Create pull request for 'size-optimization-pipeline' on GitHub'"
