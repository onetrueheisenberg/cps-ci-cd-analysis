from typing import Any, Dict, Optional


class DockerfileValidator:
    """Re-analyzes fixed Dockerfiles and compares size-only metrics."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        try:
            from .dockerfile_llm_analyzer import DockerfileAnalyzer
        except ImportError:
            from dockerfile_llm_analyzer import DockerfileAnalyzer
        self.analyzer = DockerfileAnalyzer(api_key=api_key, model=model)

    def validate_fixes(self, original_analysis: Dict[str, Any], fixed_dockerfile: str) -> Dict[str, Any]:
        import tempfile
        import os

        if not original_analysis:
            return {"success": False, "error": "Invalid original analysis"}

        if not fixed_dockerfile.strip():
            return {"success": False, "error": "Empty fixed Dockerfile"}

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".Dockerfile", delete=False) as handle:
                handle.write(fixed_dockerfile)
                temp_path = handle.name

            print("  Validating fixes...", end="", flush=True)
            fixed_analysis = self.analyzer.analyze_dockerfile(temp_path)
            print(" Done")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

        if "error" in fixed_analysis:
            return {"success": False, "error": fixed_analysis.get("error", "Validation failed")}

        original_scores = original_analysis.get("scores", {})
        fixed_scores = fixed_analysis.get("scores", {})
        improvements = self._improvement(original_scores, fixed_scores)

        return {
            "success": True,
            "original_scores": original_scores,
            "fixed_scores": fixed_scores,
            "improvements": improvements,
            "fixed_analysis": fixed_analysis,
        }

    def _improvement(self, original: Dict[str, float], fixed: Dict[str, float]) -> Dict[str, Any]:
        base = float(original.get("size_score", 0) or 0)
        new = float(fixed.get("size_score", 0) or 0)
        wasted_before = float(original.get("estimated_wasted_space_kb", 0) or 0)
        wasted_after = float(fixed.get("estimated_wasted_space_kb", 0) or 0)
        return {
            "size_score_change": round(new - base, 2),
            "wasted_space_delta_kb": round(wasted_after - wasted_before, 2),
        }

    def print_comparison_report(self, validation_results: Dict[str, Any]) -> None:
        print("\n" + "=" * 60)
        print("SIZE VALIDATION REPORT")
        print("=" * 60)
        improvements = validation_results.get("improvements", {})
        print(f"Size Score Change: {improvements.get('size_score_change', 0):.2f}")
        print(f"Wasted Space Delta (kB): {improvements.get('wasted_space_delta_kb', 0):.2f}")
        print("\n" + "=" * 60 + "\n")
