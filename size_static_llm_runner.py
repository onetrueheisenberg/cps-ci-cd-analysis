"""Run static Dockerfile analysis then size-focused LLM review."""

import argparse
import os
from typing import List

from dockerfile_optimizer import analyse_instructions, parse_dockerfile
from llm_agents.dockerfile_llm_analyzer import DockerfileAnalyzer

SIZE_KEYWORDS = (
    "size",
    "layer",
    "cache",
    "no-cache",
    "multi-stage",
    "apt-get clean",
    "rm -rf /var/lib/apt/lists",
    "--no-install-recommends",
    "--no-cache-dir",
)


def size_related(recommendations: List[dict]) -> List[dict]:
    filtered = []
    for rec in recommendations:
        message = rec.get("message", "").lower()
        if any(keyword in message for keyword in SIZE_KEYWORDS):
            filtered.append(rec)
    return filtered


def main() -> None:
    parser = argparse.ArgumentParser(description="Static + LLM size analysis for a Dockerfile")
    parser.add_argument("dockerfile", help="Path to Dockerfile")
    parser.add_argument("--model", help="Gemini model override")
    args = parser.parse_args()

    if not os.path.exists(args.dockerfile):
        raise SystemExit(f"Dockerfile not found: {args.dockerfile}")

    with open(args.dockerfile, "r", encoding="utf-8") as handle:
        contents = handle.read()

    instructions = parse_dockerfile(contents)
    static_recs = size_related(analyse_instructions(instructions))

    print("STATIC SIZE RECOMMENDATIONS:")
    if static_recs:
        for rec in static_recs:
            print(f" - [{rec.get('severity','info')}] {rec.get('message')}")
    else:
        print(" - None")

    analyzer = DockerfileAnalyzer(model=args.model)
    analysis = analyzer.analyze_dockerfile(args.dockerfile)
    analyzer.print_analysis_report(analysis)


if __name__ == "__main__":
    main()
