"""Demo pipeline to generate size-focused Dockerfile improvements.

This script runs the static size analyzer, then the LLM size analyzer
and fixer, and writes the optimized Dockerfile as a separate file so
the original remains untouched.
"""

import argparse
from pathlib import Path
from typing import Any, Dict, List

from dockerfile_optimizer import analyse_instructions, parse_dockerfile
from llm_agents.dockerfile_fixer import DockerfileFixer
from llm_agents.dockerfile_llm_analyzer import DockerfileAnalyzer


def _print_recommendations(recs: List[Dict[str, Any]]) -> None:
    if not recs:
        print("  None")
        return
    for rec in recs:
        message = rec.get("message") or ""
        severity = rec.get("severity", "info")
        print(f"  - [{severity}] {message}")


def run_pipeline(dockerfile_path: str, output_path: Path, model: str | None = None) -> Dict[str, Any]:
    dockerfile = Path(dockerfile_path)
    if not dockerfile.exists():
        return {"success": False, "error": f"Dockerfile not found: {dockerfile_path}"}

    with dockerfile.open("r", encoding="utf-8") as handle:
        original_content = handle.read()

    print("\nStep 1: Static size recommendations")
    instructions = parse_dockerfile(original_content)
    static_recs = analyse_instructions(instructions)
    _print_recommendations(static_recs)

    print("\nStep 2: LLM size optimization")
    analyzer = DockerfileAnalyzer(model=model)
    analysis = analyzer.analyze_dockerfile(str(dockerfile))
    analyzer.print_analysis_report(analysis)

    if not isinstance(analysis, dict):
        return {"success": False, "error": "Unexpected analysis response"}

    llm_analysis = analysis.get("llm_analysis", {})
    if isinstance(llm_analysis, str):
        llm_analysis = {"success": False, "error": llm_analysis, "data": {}}
        analysis["llm_analysis"] = llm_analysis

    if analysis.get("error"):
        return {"success": False, "error": analysis.get("error")}

    if not llm_analysis or not llm_analysis.get("success"):
        return {"success": False, "error": llm_analysis.get("error", "LLM analysis failed")}

    print("\nStep 3: Apply LLM size fixes")
    fixer = DockerfileFixer(api_key=analyzer.api_key, model=model)
    fix_result = fixer.fix_dockerfile(original_content, {"llm_analysis": llm_analysis})

    if not isinstance(fix_result, dict):
        return {"success": False, "error": "Unexpected fix response"}

    if not fix_result.get("success"):
        return {"success": False, "error": fix_result.get("error", "LLM fixer failed")}

    fixed_content = fix_result.get("fixed_dockerfile", "")
    output_path.write_text(fixed_content, encoding="utf-8")
    print(f"  Wrote optimized Dockerfile to {output_path}")

    return {
        "success": True,
        "original": original_content,
        "fixed": fixed_content,
        "analysis": analysis,
        "fix_result": fix_result,
        "output_path": str(output_path),
    }


def default_output_path(dockerfile_path: str, suffix: str) -> Path:
    path = Path(dockerfile_path)
    new_name = path.name + suffix if path.name != "Dockerfile" else f"Dockerfile{suffix}"
    return path.with_name(new_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run size-only Dockerfile optimization and save a copy")
    parser.add_argument("dockerfile", help="Path to the Dockerfile to analyze")
    parser.add_argument("--model", help="Gemini model override")
    parser.add_argument(
        "--suffix",
        default=".size-optimized",
        help="Filename suffix for the optimized Dockerfile copy",
    )
    parser.add_argument(
        "--output",
        help="Explicit output path for the optimized Dockerfile. Overrides --suffix when set.",
    )
    args = parser.parse_args()

    output = Path(args.output) if args.output else default_output_path(args.dockerfile, args.suffix)
    result = run_pipeline(args.dockerfile, output_path=output, model=args.model)

    if not result.get("success"):
        print(f"ERROR: {result.get('error')}")


if __name__ == "__main__":
    main()
