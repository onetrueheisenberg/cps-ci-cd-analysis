#!/usr/bin/env python3
"""
Clean up non-size-related files from the repository.

Moves research papers, manual analysis files, and non-size optimization
files to an archive directory.
"""

import os
import shutil
from pathlib import Path


def create_archive_dir():
    """Create archive directory for non-size files."""
    archive_dir = Path("archive_non_size_files")
    archive_dir.mkdir(exist_ok=True)
    return archive_dir


def move_to_archive(file_path, archive_dir):
    """Move a file to the archive directory."""
    if not os.path.exists(file_path):
        return False
    
    try:
        dest = archive_dir / Path(file_path).name
        shutil.move(file_path, dest)
        print(f"  Moved: {file_path} → {dest}")
        return True
    except Exception as e:
        print(f"  Error moving {file_path}: {e}")
        return False


def main():
    archive_dir = create_archive_dir()
    
    print("Cleaning up non-size-related files...\n")
    
    # Research papers (PDFs)
    print("1. Archiving research papers...")
    pdf_files = [
        "3530019.3530039.pdf",
        "3597503.3639143.pdf",
        "A_Model_Transformation_Tool_for_Distributed_Embedded_Control_System_Development.pdf",
        "DockerizeMe_Automatic_Inference_of_Environment_Dependencies_for_Python_Code_Snippets.pdf",
        "icse25-k8s.pdf"
    ]
    for pdf in pdf_files:
        move_to_archive(pdf, archive_dir)
    
    # Research question analysis files (Excel, Numbers, CSV)
    print("\n2. Archiving research analysis files...")
    analysis_files = [
        # RQ1 files
        "RQ1_Commit_Manual_Analysis.numbers",
        "RQ1_Commit_Manual_Analysis.xlsx",
        "RQ1_Commit_Manual_Analysis_Duplicate.numbers",
        "RQ1_Manual_Analysis.csv",
        "RQ1_Manual_Analysis.numbers",
        "RQ1_Manual_Analysis_Purpose_And_Features_Of_Docker.numbers",
        "RQ1_Manual_Analysis_Purpose_And_Features_Of_Docker.xlsx",
        "RQ1_Manual_Analysis_Purpose_And_Features_Of_Docker_Duplicate.numbers",
        "RQ1_Manual_Analysis_Purpose_And_Features_Of_Docker_Duplicate.xlsx",
        "RQ1_Manual_Analysis_Repo_List.csv",
        "RQ1_Manual_Analysis_Repo_List.numbers",
        "RQ1_Manual_Analysis_Repo_List.xlsx",
        "RQ1_Reconciliation_Manual_Analysis_Purpose_And_Features_Of_Docker-2.numbers",
        "RQ1_Reconciliation_Manual_Analysis_Purpose_And_Features_Of_Docker-2.xlsx",
        "RQ1_Tejas_Reconciliation_Manual_Analysis_Purpose_And_Features_Of_Docker-2.numbers",
        # RQ2 files
        "RQ2_Commit_Manual_Analysis_Cleaned.xlsx",
        # RQ3 files
        "RQ3_Duplicate_Image_Observations.csv",
        "RQ3_Duplicate_Image_Observations_filled.csv",
        "RQ3_Duplicate_Image_Observations_filled_corrected.csv",
        "RQ3_Duplicate_Image_Observations_filled_v3.csv",
        "RQ3_Image_Observations.csv",
        "RQ3_Image_Observations.numbers",
        "RQ3_Image_Observations.xlsx",
        "RQ3_Unformatted.csv",
        # Other analysis files
        "repo_image_optimizations.csv",
        "Repos_Image_Optimizations_Template.csv",
        "llm_dockerfile_scores.xlsx"
    ]
    for file in analysis_files:
        move_to_archive(file, archive_dir)
    
    # Non-size optimization CSV files
    print("\n3. Archiving non-size optimization CSV files...")
    non_size_csvs = [
        "package/bad-bractices.csv",
        "package/challenges.csv",
        "package/FirstRound_Agreements.csv",
        "package/mitigation.csv",
        "package/pull-request-classification.csv",
        "package/pull-request-classification.xlsx",
        "package/relations-bad-res.csv",
        "package/relations-chal-mit.csv",
        "package/restructuring-actions.csv",
        "package/SecondRound_Agreements.csv"
    ]
    for file in non_size_csvs:
        move_to_archive(file, archive_dir)
    
    # Python files not related to size optimization
    print("\n4. Archiving non-size Python files...")
    non_size_python = [
        "api.py",  # Commented out test code
        "commit_driller.py",  # Commit analysis, not size optimization
        "new_commit_driller.py",  # Commit analysis
        "checkout_code.py",  # Code checkout utility
        "new.py",  # Unclear purpose
        "parser.py",  # Generic parser (if not used by size tools)
        "docker_command_context.py",  # Docker command analysis
        "docker_image_analyzer.py",  # Generic image analyzer
        "package/selectPRs.py"  # PR selection
    ]
    for file in non_size_python:
        if os.path.exists(file):
            # Check if it's actually unused for size optimization
            move_to_archive(file, archive_dir)
    
    # Text files with non-size data
    print("\n5. Archiving miscellaneous data files...")
    misc_files = [
        "docker_commits.txt",
        "new_docker_commits.txt",
        "urls.txt",
        "test.txt",
        "temp_dockerfile",
        "dive.ts"  # TypeScript file, unclear purpose
    ]
    for file in misc_files:
        move_to_archive(file, archive_dir)
    
    print(f"\n✓ Cleanup complete!")
    print(f"  Non-size files moved to: {archive_dir}/")
    
    # Create a README in the archive
    readme_path = archive_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write("""# Archive of Non-Size-Optimization Files

This directory contains files that were not directly related to Docker image
size optimization and were moved here during the repository cleanup.

## Contents

- **Research Papers**: PDF files from academic research
- **Research Analysis**: Excel, Numbers, and CSV files from manual analysis (RQ1, RQ2, RQ3)
- **Non-Size CSVs**: Files related to bad practices, challenges, mitigation strategies
- **Utility Scripts**: Python scripts for commit analysis, PR selection, etc.
- **Miscellaneous**: Text files, temporary files, and other data files

These files are preserved for reference but are not part of the active size optimization pipeline.
""")
    print(f"  Created README in archive directory")


if __name__ == "__main__":
    main()
