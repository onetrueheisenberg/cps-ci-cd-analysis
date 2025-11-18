"""Run size-focused LLM Dockerfile optimization across repositories and export before/after waste estimates.

This script wires the llm_agents pipeline into a batch runner that:
- clones repositories from a list
- locates Dockerfiles
- runs LLM analysis + fixes
- re-analyzes the fixed Dockerfile to quantify estimated wasted kilobytes
- writes an Excel report capturing size findings before and after fixes

The script is intentionally resilient: repositories without Dockerfiles,
analysis failures, or missing dependencies are recorded as errors instead
of aborting the entire run.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from llm_agents.dockerfile_llm_analyzer import DockerfileAnalyzer, find_dockerfiles
from llm_agents.dockerfile_fixer import DockerfileFixer
from llm_agents.dockerfile_validator import DockerfileValidator


@dataclass
class SizeRecord:
    repo_url: str
    dockerfile_path: str
    original_wasted_kb: Optional[float] = None
    fixed_wasted_kb: Optional[float] = None
    wasted_space_delta_kb: Optional[float] = None
    llm_error: Optional[str] = None
    fix_error: Optional[str] = None
    validation_error: Optional[str] = None


class SizeReportRunner:
    def __init__(self, api_key: Optional[str], model: Optional[str], build_timeout: int = 300) -> None:
        self.analyzer = DockerfileAnalyzer(api_key=api_key, model=model)
        self.fixer = DockerfileFixer(api_key=api_key, model=model)
        self.validator = DockerfileValidator(api_key=api_key, model=model)
        self.build_timeout = build_timeout

    def run_for_repo(self, repo_url: str, repo_dir: Path, first_only: bool) -> List[SizeRecord]:
        dockerfiles = find_dockerfiles(str(repo_dir))
        if not dockerfiles:
            return [SizeRecord(repo_url=repo_url, dockerfile_path="", llm_error="No Dockerfiles found")]

        if first_only:
            dockerfiles = dockerfiles[:1]

        records: List[SizeRecord] = []
        for dockerfile_path in dockerfiles:
            records.append(self._record_single(repo_url, Path(dockerfile_path)))
        return records

    def _record_single(self, repo_url: str, dockerfile_path: Path) -> SizeRecord:
        original_analysis = self.analyzer.analyze_dockerfile(str(dockerfile_path))
        llm_analysis = original_analysis.get("llm_analysis", {})
        if not llm_analysis.get("success", False):
            error = llm_analysis.get("error") or original_analysis.get("error") or "LLM analysis failed"
            return SizeRecord(
                repo_url=repo_url,
                dockerfile_path=str(dockerfile_path),
                llm_error=error,
                **self._metric_fields(original_analysis.get("size_metrics", {}), prefix="original_"),
            )

        fix_result = self.fixer.fix_dockerfile(dockerfile_path.read_text(encoding="utf-8"), original_analysis)
        if not fix_result.get("success"):
            return SizeRecord(
                repo_url=repo_url,
                dockerfile_path=str(dockerfile_path),
                fix_error=fix_result.get("error", "Failed to generate fix"),
                **self._metric_fields(original_analysis.get("size_metrics", {}), prefix="original_"),
            )

        validation = self.validator.validate_fixes(original_analysis, fix_result["fixed_dockerfile"])
        fixed_metrics = validation.get("fixed_metrics", {})
        improvements = validation.get("improvements", {})
        record = SizeRecord(
            repo_url=repo_url,
            dockerfile_path=str(dockerfile_path),
            **self._metric_fields(original_analysis.get("size_metrics", {}), prefix="original_"),
            **self._metric_fields(fixed_metrics, prefix="fixed_"),
            wasted_space_delta_kb=self._improvement(improvements, "wasted_space_delta_kb"),
        )

        if not validation.get("success"):
            record.validation_error = validation.get("error", "Validation failed")

        return record

    @staticmethod
    def _metric_fields(metrics: Dict[str, float], prefix: str) -> Dict[str, Optional[float]]:
        return {
            f"{prefix}wasted_kb": metrics.get("estimated_wasted_space_kb"),
        }

    @staticmethod
    def _improvement(improvements: Dict[str, float], key: str) -> Optional[float]:
        return improvements.get(key)


def read_repo_list(repos_file: Path) -> List[str]:
    urls: List[str] = []
    with repos_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("http"):
                urls.append(line)
            else:
                parts = [p.strip() for p in line.split(",") if "http" in p]
                urls.extend(parts)
    return urls


def clone_repo(repo_url: str, base_dir: Path) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    dest = base_dir / repo_name
    if dest.exists():
        return dest

    subprocess.run(["git", "clone", "--depth", "1", repo_url, str(dest)], check=False)
    return dest


def export_size_report(records: Sequence[SizeRecord], output_path: Path) -> None:
    rows = [asdict(r) for r in records]

    try:
        import pandas as pd

        df = pd.DataFrame(rows)
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="size_metrics")
            meta = pd.DataFrame(
                {
                    "run_timestamp": [dt.datetime.utcnow().isoformat() + "Z"],
                    "repo_count": [len({r.repo_url for r in records})],
                    "dockerfile_count": [len(records)],
                }
            )
            meta.to_excel(writer, index=False, sheet_name="run_metadata")
        return
    except ImportError:
        pass

    try:
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "size_metrics"

        headers = list(rows[0].keys()) if rows else []
        if headers:
            ws.append(headers)
            for row in rows:
                ws.append([row.get(h) for h in headers])

        meta_ws = wb.create_sheet("run_metadata")
        meta_ws.append(["run_timestamp", "repo_count", "dockerfile_count"])
        meta_ws.append([dt.datetime.utcnow().isoformat() + "Z", len({r.repo_url for r in records}), len(records)])

        wb.save(output_path)
        return
    except Exception as exc:  # pragma: no cover - best-effort fallback
        sys.stderr.write(f"Failed to write Excel file: {exc}\n")

    csv_path = output_path.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Batch LLM Dockerfile size report generator")
    parser.add_argument("--repos-file", default="docker_repos.txt", help="File with repository URLs (default: docker_repos.txt)")
    parser.add_argument("--output", default="llm_dockerfile_sizes.xlsx", help="Excel output path (default: llm_dockerfile_sizes.xlsx)")
    parser.add_argument("--clone-dir", default="cloned_repos", help="Directory to place cloned repositories")
    parser.add_argument("--keep-cloned", action="store_true", help="Keep cloned repositories after processing")
    parser.add_argument("--first-only", action="store_true", help="Analyze only the first Dockerfile found in each repo")
    parser.add_argument("--api-key", default=None, help="Gemini API key (default: env GEMINI_API_KEY or GOOGLE_API_KEY)")
    parser.add_argument("--model", default=None, help="Gemini model name (default: env GEMINI_MODEL)")
    parser.add_argument("--build-timeout", type=int, default=300, help="Docker build timeout for tests (default: 300)")
    args = parser.parse_args(argv)

    api_key = args.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model = args.model or os.getenv("GEMINI_MODEL")

    repos = read_repo_list(Path(args.repos_file))
    clone_dir = Path(args.clone_dir)

    runner = SizeReportRunner(api_key=api_key, model=model, build_timeout=args.build_timeout)

    records: List[SizeRecord] = []
    for idx, repo_url in enumerate(repos, start=1):
        print(f"[{idx}/{len(repos)}] Processing {repo_url}")
        repo_path = clone_repo(repo_url, clone_dir)
        try:
            records.extend(runner.run_for_repo(repo_url, repo_path, args.first_only))
        finally:
            if not args.keep_cloned and repo_path.exists():
                shutil.rmtree(repo_path)

    export_size_report(records, Path(args.output))
    print(f"\nWrote size report for {len(records)} Dockerfile(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
