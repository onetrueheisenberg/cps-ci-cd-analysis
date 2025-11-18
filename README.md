# CPS CI/CD Analysis

This repository contains utilities for analyzing Dockerfiles and Docker images, along with an LLM-driven pipeline that now focuses **only on image size**. The `llm_size_report.py` script clones the repository list, runs the size-only LLM pipeline, and exports a size report to Excel for comparing estimated waste before and after fixes.

## Prerequisites
- Python 3.10+
- Docker installed and available on your PATH (required for validation/tests)
- Git installed (for cloning repositories)
- Network access to GitHub and the Gemini API
- A Google Gemini API key exported as `GEMINI_API_KEY` or `GOOGLE_API_KEY` (optional `GEMINI_MODEL` to override the default model)
- Python dependencies:
  ```bash
  pip install google-generativeai pandas openpyxl python-dotenv
  ```

## Inputs
- `docker_repos.txt` should contain one repository URL per line (or comma-separated on a line). The default list includes the 99 repositories used for the study.
- Dockerfiles will be cloned into `cloned_repos` by default; use `--clone-dir` to change the location.

## Quick one-liner to apply size fixes
Analyze a Dockerfile for size waste, apply the LLM-generated fixes directly to the file (with a `.bak` backup), and skip optional Docker build tests:

```bash
python -m llm_agents.dockerfile_pipeline path/to/Dockerfile --apply --skip-test
```

## Apply size fixes across many repositories (writes separate copies)
Run the analyzer and LLM fixer for every Dockerfile in your repo list, writing optimized copies alongside the originals using a suffix. This keeps the source Dockerfiles untouched while collecting the size-focused variants:

```bash
python llm_size_apply.py --repos-file docker_repos.txt --export-dir optimized_dockerfiles --suffix .llm-size
```

- Change `--suffix` if you prefer a different filename marker.
- Drop `--export-dir` to keep only the in-repo copies; add `--first-only` to process just the first Dockerfile per repo.

## Running the size report pipeline
1. Ensure prerequisites are installed and the Gemini API key is set in your environment (or a `.env` file loaded via `python-dotenv`).
2. Run the pipeline (analyzes the first Dockerfile per repo by default) to get **size-only** wasted-space estimates before and after fixes:
   ```bash
   python llm_size_report.py \
     --repos-file docker_repos.txt \
     --output llm_dockerfile_sizes.xlsx \
     --clone-dir cloned_repos \
     --first-only
   ```
3. To process every Dockerfile in each repo, omit `--first-only`:
   ```bash
   python llm_size_report.py --repos-file docker_repos.txt --output llm_dockerfile_sizes.xlsx
   ```
4. Add `--keep-cloned` if you want to preserve the cloned repositories for inspection.

### One-off size review for a single Dockerfile
If you only need size-related recommendations for one Dockerfile without writing changes, run the static analyzer first and then the size-focused LLM helper:

```bash
python size_static_llm_runner.py path/to/Dockerfile [--model <gemini-model>]
```

The script prints static recommendations filtered to size waste and then an LLM report with estimated wasted kilobytes.

## Outputs
- An Excel workbook (or CSV fallback) with before/after estimated wasted kilobytes and run metadata. The default file is `llm_dockerfile_sizes.xlsx` written to the repository root.

## Troubleshooting
- If Excel dependencies are missing, install `pandas` and `openpyxl`, or rely on the CSV fallback generated alongside the requested output path.
- If Docker is unavailable, the validator and tester will be skipped; reports will still be produced from static analysis but build/run checks will be missing.
