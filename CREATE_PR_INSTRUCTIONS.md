# Creating a Pull Request for Size Optimization Changes

This document provides step-by-step instructions to create a branch and pull request
for the size optimization pipeline changes.

## Changes Made

### 1. **New Size Optimization Pipeline** (`size_optimization_pipeline.py`)
   - Comprehensive pipeline for processing repositories through static and LLM-based size optimizations
   - Saves Dockerfiles at each stage: original, post-static, post-LLM
   - Tracks size savings estimates at each optimization step
   - Outputs detailed CSV results with savings metrics

### 2. **Cleanup of Non-Size Files** (`cleanup_non_size_files.py`)
   - Moved all non-size-related files to `archive_non_size_files/`
   - Archived: research papers, manual analysis files, non-size CSVs, utility scripts
   - Created archive README for documentation

### 3. **Project Configuration Updates**
   - Added `requirements.txt` with dependencies
   - Updated `.gitignore` for Python project structure
   - Created `demo.py` for quick demonstrations
   - Updated `replit.md` with project documentation

### 4. **Archived Files**
   - 50+ files moved to `archive_non_size_files/`
   - All research papers (PDFs)
   - RQ1, RQ2, RQ3 analysis files
   - Non-size optimization CSVs
   - Utility scripts not related to size optimization

## Git Commands to Create PR

### Step 1: Verify Current State
```bash
# Check which branch you're on
git branch

# Check what files have changed
git status
```

### Step 2: Create a New Branch
```bash
# Create and switch to a new branch for size optimization
git checkout -b size-optimization-pipeline
```

### Step 3: Stage All Changes
```bash
# Add all new and modified files
git add .

# Or add specific files/directories
git add size_optimization_pipeline.py
git add cleanup_non_size_files.py
git add archive_non_size_files/
git add requirements.txt
git add .gitignore
git add demo.py
git add replit.md
git add CREATE_PR_INSTRUCTIONS.md
git add GIT_COMMIT_SCRIPT.sh
```

### Step 4: Commit Changes
```bash
git commit -m "Add size optimization pipeline and cleanup non-size files

- Created comprehensive size optimization pipeline combining static and LLM analysis
- Added filter for size-related recommendations only
- Track and save Dockerfiles at each optimization stage (original, static, LLM)
- Calculate and report potential size savings in KB/MB
- Moved non-size files (research papers, analysis data, utility scripts) to archive
- Updated project documentation and configuration
- Added demo script and improved .gitignore"
```

### Step 5: Push to GitHub
```bash
# Push the new branch to GitHub
git push -u origin size-optimization-pipeline
```

### Step 6: Create Pull Request
After pushing, GitHub will provide a URL to create a pull request. Alternatively:

1. Go to: https://github.com/onetrueheisenberg/cps-ci-cd-analysis
2. Click "Pull requests" tab
3. Click "New pull request"
4. Select base: `main` and compare: `size-optimization-pipeline`
5. Add PR details:

**Title:**
```
Size Optimization Pipeline - Static and LLM-based Docker Image Size Optimization
```

**Description:**
```markdown
## Overview
This PR introduces a comprehensive size optimization pipeline for Docker images,
combining static analysis with LLM-based optimization, and cleans up non-size-related files.

## Key Changes

### 1. Size Optimization Pipeline (`size_optimization_pipeline.py`)
- **Two-stage optimization**: Static analysis followed by LLM-based refinement
- **Size-focused filtering**: Only applies size-related optimizations (excludes security, general performance)
- **Dockerfile tracking**: Saves original, static-optimized, and LLM-optimized versions
- **Savings estimation**: Calculates potential KB/MB savings at each stage
- **CSV results**: Detailed report with per-repo optimization metrics

### 2. Static Optimization Features
- Filters for size-related recommendations only
- Applies automatic fixes:
  - Adds `--no-install-recommends` to apt-get
  - Adds `--no-cache-dir` to pip install
  - Adds apt cache cleanup (`rm -rf /var/lib/apt/lists/*`)
  - Suggests multi-stage builds for large images

### 3. LLM Optimization Features
- Size-focused analysis using Gemini API
- Builds on static optimizations
- Conservative approach (only fixes identified issues)
- Estimates wasted space and layer efficiency

### 4. File Cleanup
- Moved 50+ non-size-related files to `archive_non_size_files/`
- Archived: research papers, RQ analysis files, non-size CSVs, utility scripts
- Created archive README for documentation
- Focused repository on size optimization only

### 5. Project Configuration
- Added `requirements.txt` for dependency management
- Updated `.gitignore` for Python projects
- Created demo script for quick testing
- Updated project documentation

## Usage

### Run the full pipeline on all repos:
```bash
python size_optimization_pipeline.py --repos-file docker_repos.txt
```

### Run with limited repos for testing:
```bash
python size_optimization_pipeline.py --limit 5
```

### Specify custom output directory:
```bash
python size_optimization_pipeline.py --output-dir my_optimized_dockerfiles
```

## Output
- **Optimized Dockerfiles**: `optimized_dockerfiles/` directory
- **Results CSV**: `size_optimization_results.csv` with metrics
- **Per-repo tracking**: Original, static, and LLM optimized versions

## Files Archived
All non-size-related files moved to `archive_non_size_files/`:
- Research papers (PDFs)
- Manual analysis files (RQ1, RQ2, RQ3 Excel/CSV/Numbers)
- Non-size optimization data (challenges, mitigation, etc.)
- Utility scripts (commit analysis, PR selection, etc.)

## Dependencies
- google-generativeai (for LLM optimization)
- pandas (for CSV processing)
- openpyxl (for Excel export)
- python-dotenv (for environment management)

All dependencies listed in `requirements.txt`.

## Testing
Tested on the project's example Dockerfile with successful optimization and size savings estimation.
```

6. Click "Create pull request"

## Alternative: Using GitHub CLI

If you have GitHub CLI installed:

```bash
# Create PR directly from command line
gh pr create --title "Size Optimization Pipeline - Static and LLM-based Docker Image Size Optimization" \
  --body-file PR_DESCRIPTION.md \
  --base main \
  --head size-optimization-pipeline
```

## Verification Before Creating PR

```bash
# View all changes
git diff main...size-optimization-pipeline

# View file changes summary
git diff --stat main...size-optimization-pipeline

# Test the pipeline (optional, with limited repos)
python size_optimization_pipeline.py --limit 2
```

## Notes

- The `GEMINI_API_KEY` is stored in Replit Secrets and will work when running the pipeline
- The pipeline can process all 99 repositories but may take significant time
- Consider running with `--limit` flag for initial testing
- All non-size files are preserved in the archive directory
