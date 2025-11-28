#!/usr/bin/env python3
"""
Demo script for the Dockerfile Analysis Tool

This script demonstrates how to use the LLM-powered Dockerfile analyzer.
"""
import os
import sys
from pathlib import Path

def print_banner():
    print("=" * 70)
    print("  Docker Image Analyzer - LLM-Powered Dockerfile Analysis")
    print("=" * 70)
    print()

def check_api_key():
    # api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    api_key='AIzaSyAjjpS9apfIUPyz3Wv6PS3rSSq_ylQG-TI'
    if not api_key:
        print("❌ ERROR: No Gemini API key found!")
        print("Please set the GEMINI_API_KEY environment variable.")
        print()
        return False
    print("✓ Gemini API key found")
    return True

def main():
    print_banner()
    
    if not check_api_key():
        sys.exit(1)
    
    print()
    print("Available Commands:")
    print("-" * 70)
    print()
    print("1. Analyze the project's Dockerfile:")
    print("   python size_static_llm_runner.py Dockerfile")
    print()
    print("2. Run the full scorecard pipeline (analyzes repos in docker_repos.txt):")
    print("   python llm_scorecard.py --repos-file docker_repos.txt --first-only")
    print()
    print("3. Analyze a specific Dockerfile:")
    print("   python dockerfile_optimizer.py --repo-path /path/to/repo")
    print()
    print("-" * 70)
    print()
    print("Quick Demo: Analyzing the project's Dockerfile...")
    print()
    
    if Path("Dockerfile").exists():
        print("Running analysis on ./Dockerfile...")
        print()
        os.system("python size_static_llm_runner.py Dockerfile")
    else:
        print("No Dockerfile found in current directory.")
        print()
        print("To analyze Dockerfiles from GitHub repositories, run:")
        print("  python llm_scorecard.py --repos-file docker_repos.txt --first-only")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
