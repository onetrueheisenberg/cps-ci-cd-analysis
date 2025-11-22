# CPS CI/CD Analysis - Dockerfile Analyzer

## Overview
This is a Python-based research tool for analyzing Dockerfiles using Google's Gemini AI. It provides LLM-powered analysis of Dockerfile quality, security risks, performance issues, and optimization opportunities.

## Purpose
The tool was created for analyzing Docker adoption in Cyber-Physical Systems (CPS) projects. It can:
- Analyze individual Dockerfiles for best practices, security, and efficiency
- Score Dockerfiles before and after automated fixes
- Batch process multiple repositories to compare Docker usage patterns
- Generate Excel reports with detailed metrics

## Current State
✅ **Fully configured and working!**
- Python 3.11 installed with all dependencies
- Gemini API key configured in secrets
- Demo workflow set up and tested
- Successfully analyzed the project's example Dockerfile

## Recent Changes (2024-11-22)
- Installed Python 3.11 and required dependencies
- Created `requirements.txt` for dependency management
- Updated `.gitignore` for Python project structure
- Configured Gemini API key from user
- Created `demo.py` workflow to demonstrate tool capabilities
- Tested the analyzer successfully on the project's Dockerfile

## Project Architecture

### Main Components
1. **LLM Agents** (`llm_agents/` directory):
   - `dockerfile_llm_analyzer.py`: Core LLM-based analysis using Gemini
   - `dockerfile_fixer.py`: Automated Dockerfile optimization
   - `dockerfile_validator.py`: Validation of fixes
   - `dockerfile_tester.py`: Docker build/run testing
   - `dockerfile_pipeline.py`: Orchestrates the full analysis pipeline

2. **Analysis Scripts**:
   - `llm_scorecard.py`: Batch analyzer for multiple repos
   - `size_static_llm_runner.py`: Size optimization analysis
   - `dockerfile_optimizer.py`: Static analysis and recommendations
   - `demo.py`: Demo script for quick testing

3. **Data**:
   - `docker_repos.txt`: List of 99 CPS repositories to analyze
   - `package/`: Research data and classifications

### Technology Stack
- **Language**: Python 3.11
- **LLM**: Google Gemini AI (gemini-2.5-flash-lite)
- **Analysis**: Static + LLM-based Docker analysis
- **Output**: Excel/CSV reports with pandas

## How to Use

### Quick Start (Demo)
The demo workflow runs automatically and shows:
```bash
python demo.py
```

### Analyze a Single Dockerfile
```bash
python size_static_llm_runner.py Dockerfile
```

### Run Full Scorecard Pipeline
Analyze repositories listed in `docker_repos.txt`:
```bash
python llm_scorecard.py --repos-file docker_repos.txt --first-only --output results.xlsx
```

### Analyze a Local Repository
```bash
python dockerfile_optimizer.py --repo-path /path/to/repo
```

## Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key (configured in secrets)
- `GEMINI_MODEL`: Optional model override (default: gemini-2.5-flash-lite)

## User Preferences
- None specified yet

## Dependencies
See `requirements.txt`:
- google-generativeai (LLM integration)
- pandas (data processing)
- openpyxl (Excel export)
- python-dotenv (environment management)

## Notes
- Docker is optional but recommended for validation/testing features
- Without Docker, the tool still provides static and LLM-based analysis
- Git is required for cloning repositories in batch mode
- The tool is designed to be resilient - errors in individual repos don't stop the batch process
