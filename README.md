# CPS CI/CD Analysis

This repository contains utilities for analyzing Dockerfiles and Docker images, along with an LLM-driven pipeline that scores Dockerfiles before and after automated fixes. The `llm_scorecard.py` script clones the repository list, runs the LLM pipeline, and exports a scorecard to Excel for comparing improvements across the supplied Dockerfiles.

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

## Running the scorecard pipeline
1. Ensure prerequisites are installed and the Gemini API key is set in your environment (or a `.env` file loaded via `python-dotenv`).
2. Run the pipeline (analyzes the first Dockerfile per repo by default):
   ```bash
   python llm_scorecard.py \
     --repos-file docker_repos.txt \
     --output llm_dockerfile_scores.xlsx \
     --clone-dir cloned_repos \
     --first-only
   ```
3. To process every Dockerfile in each repo, omit `--first-only`:
   ```bash
   python llm_scorecard.py --repos-file docker_repos.txt --output llm_dockerfile_scores.xlsx
   ```
4. Add `--keep-cloned` if you want to preserve the cloned repositories for inspection.

## Outputs
- An Excel workbook (or CSV fallback) with before/after LLM scores, issue counts, and run metadata. The default file is `llm_dockerfile_scores.xlsx` written to the repository root.

## Troubleshooting
- If Excel dependencies are missing, install `pandas` and `openpyxl`, or rely on the CSV fallback generated alongside the requested output path.
- If Docker is unavailable, the validator and tester will be skipped; scores will still be produced from static analysis but build/run checks will be missing.
