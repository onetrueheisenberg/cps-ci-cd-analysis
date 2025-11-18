"""Batch-apply size-focused LLM Dockerfile fixes without overwriting originals.

This helper clones repositories, runs the size analyzer, generates
LLM-backed fixes, and writes each optimized Dockerfile alongside the
original using a configurable suffix. Optionally, optimized files can be
exported to an output directory for safekeeping.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Sequence

from llm_agents.dockerfile_llm_analyzer import DockerfileAnalyzer, find_dockerfiles
from llm_agents.dockerfile_fixer import DockerfileFixer


def read_repo_list(repos_file: Path) -> List[str]:
    urls: List[str] = []
    with repos_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("http"):
                urls.append(line)
            else:
                urls.extend([part.strip() for part in line.split(",") if part.strip().startswith("http")])
    return urls


def clone_repo(repo_url: str, base_dir: Path) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    dest = base_dir / repo_name
    if dest.exists():
        return dest
    subprocess.run(["git", "clone", "--depth", "1", repo_url, str(dest)], check=False)
    return dest


def write_optimized_copy(
    original_path: Path,
    optimized_contents: str,
    suffix: str,
    export_root: Optional[Path],
    repo_root: Path,
) -> Path:
    target_path = original_path.with_name(original_path.name + suffix)
    target_path.write_text(optimized_contents, encoding="utf-8")

    if export_root:
        export_root.mkdir(parents=True, exist_ok=True)
        relative = original_path.relative_to(repo_root)
        export_path = export_root / relative.with_name(relative.name + suffix)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(optimized_contents, encoding="utf-8")
    return target_path


def process_dockerfile(
    dockerfile_path: Path,
    analyzer: DockerfileAnalyzer,
    fixer: DockerfileFixer,
    suffix: str,
    export_root: Optional[Path],
    repo_root: Path,
) -> None:
    print(f"  Analyzing {dockerfile_path}")
    analysis = analyzer.analyze_dockerfile(str(dockerfile_path))
    llm_analysis = analysis.get("llm_analysis", {})
    if not llm_analysis.get("success"):
        print(f"    Skipped (analysis failed): {llm_analysis.get('error', 'Unknown error')}")
        return

    fix_result = fixer.fix_dockerfile(dockerfile_path.read_text(encoding="utf-8"), analysis)
    if not fix_result.get("success"):
        print(f"    Skipped (fix failed): {fix_result.get('error', 'Unknown error')}")
        return

    optimized_path = write_optimized_copy(
        dockerfile_path,
        fix_result["fixed_dockerfile"],
        suffix=suffix,
        export_root=export_root,
        repo_root=repo_root,
    )
    print(f"    Wrote optimized copy -> {optimized_path}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Apply size-focused LLM fixes to Dockerfiles across repos")
    parser.add_argument("--repos-file", default="docker_repos.txt", help="Text file with repository URLs (default: docker_repos.txt)")
    parser.add_argument("--clone-dir", default="cloned_repos", help="Directory to place cloned repositories")
    parser.add_argument("--keep-cloned", action="store_true", help="Keep cloned repositories after processing")
    parser.add_argument("--suffix", default=".llm-size", help="Suffix for optimized Dockerfile copies (default: .llm-size)")
    parser.add_argument("--export-dir", default=None, help="Optional directory to also store optimized copies outside the repo")
    parser.add_argument("--first-only", action="store_true", help="Only process the first Dockerfile found in each repo")
    parser.add_argument("--api-key", default=None, help="Gemini API key (default: env GEMINI_API_KEY or GOOGLE_API_KEY)")
    parser.add_argument("--model", default=None, help="Gemini model override")
    args = parser.parse_args(argv)

    api_key = args.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model = args.model or os.getenv("GEMINI_MODEL")

    analyzer = DockerfileAnalyzer(api_key=api_key, model=model)
    fixer = DockerfileFixer(api_key=api_key, model=model)

    repos = read_repo_list(Path(args.repos_file))
    clone_dir = Path(args.clone_dir)
    export_root = Path(args.export_dir) if args.export_dir else None

    for idx, repo_url in enumerate(repos, start=1):
        print(f"[{idx}/{len(repos)}] Processing {repo_url}")
        repo_path = clone_repo(repo_url, clone_dir)
        dockerfiles = find_dockerfiles(str(repo_path))
        if not dockerfiles:
            print("  No Dockerfiles found")
        else:
            to_process = dockerfiles[:1] if args.first_only else dockerfiles
            for dockerfile in to_process:
                process_dockerfile(Path(dockerfile), analyzer, fixer, args.suffix, export_root, repo_path)
        if not args.keep_cloned and repo_path.exists():
            shutil.rmtree(repo_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
