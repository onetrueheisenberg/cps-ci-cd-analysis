import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

if __package__ is None or __package__ == "":
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from dockerfile_llm_analyzer import DockerfileAnalyzer, find_dockerfiles
    from dockerfile_fixer import DockerfileFixer
    from dockerfile_validator import DockerfileValidator
    from dockerfile_tester import DockerfileTester
else:
    from .dockerfile_llm_analyzer import DockerfileAnalyzer, find_dockerfiles
    from .dockerfile_fixer import DockerfileFixer
    from .dockerfile_validator import DockerfileValidator
    from .dockerfile_tester import DockerfileTester


class DockerfilePipeline:
    """Runs size-focused analysis, fixing, validation, and optional build tests."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, build_timeout: int = 300):
        self.analyzer = DockerfileAnalyzer(api_key=api_key, model=model)
        self.fixer = DockerfileFixer(api_key=api_key, model=model)
        self.validator = DockerfileValidator(api_key=api_key, model=model)
        self.tester = DockerfileTester(build_timeout=build_timeout)

    def optimize_dockerfile(self, dockerfile_path: str, skip_test: bool = False) -> Dict[str, Any]:
        results: Dict[str, Any] = {"dockerfile_path": dockerfile_path, "stages": {}}

        print("\n" + "=" * 60)
        print("STAGE 1: SIZE ANALYSIS")
        print("=" * 60)
        analysis = self.analyzer.analyze_dockerfile(dockerfile_path)
        results["stages"]["analysis"] = {"success": "error" not in analysis, "result": analysis}
        if "error" in analysis:
            return results

        with open(dockerfile_path, "r", encoding="utf-8") as handle:
            original_content = handle.read()

        print("\n" + "=" * 60)
        print("STAGE 2: APPLY SIZE FIXES")
        print("=" * 60)
        fix_result = self.fixer.fix_dockerfile(original_content, analysis)
        results["stages"]["fix"] = {"success": fix_result.get("success", False), "result": fix_result}
        if not fix_result.get("success"):
            return results
        fixed_content = fix_result["fixed_dockerfile"]

        print("\n" + "=" * 60)
        print("STAGE 3: VALIDATE SIZE IMPROVEMENT")
        print("=" * 60)
        validation = self.validator.validate_fixes(analysis, fixed_content)
        results["stages"]["validation"] = {"success": validation.get("success", False), "result": validation}

        if not skip_test:
            print("\n" + "=" * 60)
            print("STAGE 4: OPTIONAL BUILD TEST")
            print("=" * 60)
            if not self.tester.docker_available:
                results["stages"]["test"] = {"success": None, "skipped": True, "reason": "Docker CLI not available"}
            else:
                test_result = self.tester.test_dockerfile(
                    fixed_content,
                    dockerfile_path,
                    os.path.dirname(dockerfile_path) or ".",
                )
                results["stages"]["test"] = {"success": test_result.get("success", False), "result": test_result}

        results["original_dockerfile"] = original_content
        results["fixed_dockerfile"] = fixed_content
        results["original_analysis"] = analysis
        results["success"] = results["stages"]["analysis"].get("success") and results["stages"]["fix"].get("success")
        return results

    def print_pipeline_report(self, results: Dict[str, Any]) -> None:
        print("\n" + "=" * 60)
        print("PIPELINE REPORT (SIZE ONLY)")
        print("=" * 60)
        if not results.get("success"):
            print("Pipeline failed to complete all stages.")
            return

        validation = results.get("stages", {}).get("validation", {}).get("result", {})
        if validation and validation.get("success"):
            self.validator.print_comparison_report(validation)

        print("Fixed Dockerfile Preview:\n")
        fixed = results.get("fixed_dockerfile", "")
        print(fixed[:800] + ("..." if len(fixed) > 800 else ""))
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Size-focused Dockerfile optimization pipeline")
    parser.add_argument("dockerfile", help="Path to Dockerfile")
    parser.add_argument("--skip-test", action="store_true", help="Skip docker build test")
    parser.add_argument("--model", help="Override Gemini model")
    parser.add_argument("--apply", action="store_true", help="Write the optimized Dockerfile back to disk")
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a .bak copy before applying changes",
    )
    args = parser.parse_args()

    pipeline = DockerfilePipeline(model=args.model)
    outcome = pipeline.optimize_dockerfile(args.dockerfile, skip_test=args.skip_test)
    pipeline.print_pipeline_report(outcome)

    fixed_content = outcome.get("fixed_dockerfile") if outcome else None
    if args.apply and outcome.get("success") and fixed_content:
        if not args.no_backup:
            backup_path = f"{args.dockerfile}.bak"
            shutil.copy(args.dockerfile, backup_path)
            print(f"Backup written to {backup_path}")

        with open(args.dockerfile, "w", encoding="utf-8") as handle:
            handle.write(fixed_content)
        print(f"Applied size fixes to {args.dockerfile}")
    elif args.apply:
        print("Skipping write-back: no fixed Dockerfile produced.")
