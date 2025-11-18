"""Run LLM-driven Dockerfile optimization across repositories and export before/after scores.

This script wires the llm_agents pipeline into a batch runner that:
- clones repositories from a list
- locates Dockerfiles
- runs LLM analysis + fixes
- re-analyzes the fixed Dockerfile to quantify improvements
- writes an Excel scorecard for comparing before/after scores

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
class ScoreRecord:
    repo_url: str
    dockerfile_path: str
    original_overall: Optional[float] = None
    original_security: Optional[float] = None
    original_efficiency: Optional[float] = None
    original_best_practices: Optional[float] = None
    original_complexity: Optional[float] = None
    original_maintainability: Optional[float] = None
    original_wasted_kb: Optional[float] = None
    fixed_overall: Optional[float] = None
    fixed_security: Optional[float] = None
    fixed_efficiency: Optional[float] = None
    fixed_best_practices: Optional[float] = None
    fixed_complexity: Optional[float] = None
    fixed_maintainability: Optional[float] = None
    fixed_wasted_kb: Optional[float] = None
    improvement_overall: Optional[float] = None
    improvement_security: Optional[float] = None
    improvement_efficiency: Optional[float] = None
    improvement_best_practices: Optional[float] = None
    security_risks_before: Optional[int] = None
    security_risks_after: Optional[int] = None
    performance_issues_before: Optional[int] = None
    performance_issues_after: Optional[int] = None
    missing_practices_before: Optional[int] = None
    missing_practices_after: Optional[int] = None
    llm_error: Optional[str] = None
    fix_error: Optional[str] = None
    validation_error: Optional[str] = None


class ScorecardRunner:
    def __init__(self, api_key: Optional[str], model: Optional[str], build_timeout: int = 300) -> None:
        self.analyzer = DockerfileAnalyzer(api_key=api_key, model=model)
        self.fixer = DockerfileFixer(api_key=api_key, model=model)
        self.validator = DockerfileValidator(api_key=api_key, model=model)
        self.build_timeout = build_timeout

    def run_for_repo(self, repo_url: str, repo_dir: Path, first_only: bool) -> List[ScoreRecord]:
        dockerfiles = find_dockerfiles(str(repo_dir))
        if not dockerfiles:
            return [ScoreRecord(repo_url=repo_url, dockerfile_path="", llm_error="No Dockerfiles found")]

        if first_only:
            dockerfiles = dockerfiles[:1]

        records: List[ScoreRecord] = []
        for dockerfile_path in dockerfiles:
            records.append(self._score_single(repo_url, Path(dockerfile_path)))
        return records

    def _score_single(self, repo_url: str, dockerfile_path: Path) -> ScoreRecord:
        original_analysis = self.analyzer.analyze_dockerfile(str(dockerfile_path))
        llm_analysis = original_analysis.get("llm_analysis", {})
        if not llm_analysis.get("success", False):
            error = llm_analysis.get("error") or original_analysis.get("error") or "LLM analysis failed"
            return ScoreRecord(
                repo_url=repo_url,
                dockerfile_path=str(dockerfile_path),
                llm_error=error,
                **self._score_fields(original_analysis.get("scores", {}), prefix="original_"),
            )

        fix_result = self.fixer.fix_dockerfile(dockerfile_path.read_text(encoding="utf-8"), original_analysis)
        if not fix_result.get("success"):
            return ScoreRecord(
                repo_url=repo_url,
                dockerfile_path=str(dockerfile_path),
                fix_error=fix_result.get("error", "Failed to generate fix"),
                **self._score_fields(original_analysis.get("scores", {}), prefix="original_"),
            )

        validation = self.validator.validate_fixes(original_analysis, fix_result["fixed_dockerfile"])
        fixed_scores = validation.get("fixed_scores", {})
        improvements = validation.get("improvements", {})
        issues = validation.get("issues_comparison", {})

        record = ScoreRecord(
            repo_url=repo_url,
            dockerfile_path=str(dockerfile_path),
            **self._score_fields(original_analysis.get("scores", {}), prefix="original_"),
            **self._score_fields(fixed_scores, prefix="fixed_"),
            improvement_overall=self._improvement(improvements, "overall_score"),
            improvement_security=self._improvement(improvements, "security_score"),
            improvement_efficiency=self._improvement(improvements, "efficiency_score"),
            improvement_best_practices=self._improvement(improvements, "best_practices_score"),
            security_risks_before=self._issue_count(issues, "security_risks", "original_count"),
            security_risks_after=self._issue_count(issues, "security_risks", "fixed_count"),
            performance_issues_before=self._issue_count(issues, "performance_issues", "original_count"),
            performance_issues_after=self._issue_count(issues, "performance_issues", "fixed_count"),
            missing_practices_before=self._issue_count(issues, "missing_practices", "original_count"),
            missing_practices_after=self._issue_count(issues, "missing_practices", "fixed_count"),
        )

        if not validation.get("success"):
            record.validation_error = validation.get("error", "Validation failed")

        return record

    @staticmethod
    def _score_fields(scores: Dict[str, float], prefix: str) -> Dict[str, Optional[float]]:
        return {
            f"{prefix}overall": scores.get("overall_score"),
            f"{prefix}security": scores.get("security_score"),
            f"{prefix}efficiency": scores.get("efficiency_score"),
            f"{prefix}best_practices": scores.get("best_practices_score"),
            f"{prefix}complexity": scores.get("complexity_score"),
            f"{prefix}maintainability": scores.get("maintainability_score"),
            f"{prefix}wasted_kb": scores.get("estimated_wasted_space_kb"),
        }

    @staticmethod
    def _improvement(improvements: Dict[str, Dict[str, float]], key: str) -> Optional[float]:
        if key not in improvements:
            return None
        return improvements[key].get("improvement")

    @staticmethod
    def _issue_count(issues: Dict[str, Dict[str, int]], section: str, field: str) -> Optional[int]:
        return issues.get(section, {}).get(field)


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


def export_scorecard(records: Sequence[ScoreRecord], output_path: Path) -> None:
    rows = [asdict(r) for r in records]

    try:
        import pandas as pd

        df = pd.DataFrame(rows)
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="scores")
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
        ws.title = "scores"

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
    parser = argparse.ArgumentParser(description="Batch LLM Dockerfile scorecard generator")
    parser.add_argument("--repos-file", default="docker_repos.txt", help="File with repository URLs (default: docker_repos.txt)")
    parser.add_argument("--output", default="llm_dockerfile_scores.xlsx", help="Excel output path (default: llm_dockerfile_scores.xlsx)")
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

    runner = ScorecardRunner(api_key=api_key, model=model, build_timeout=args.build_timeout)

    records: List[ScoreRecord] = []
    for idx, repo_url in enumerate(repos, start=1):
        print(f"[{idx}/{len(repos)}] Processing {repo_url}")
        repo_path = clone_repo(repo_url, clone_dir)
        try:
            records.extend(runner.run_for_repo(repo_url, repo_path, args.first_only))
        finally:
            if not args.keep_cloned and repo_path.exists():
                shutil.rmtree(repo_path)

    export_scorecard(records, Path(args.output))
    print(f"\nWrote scorecard for {len(records)} Dockerfile(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
