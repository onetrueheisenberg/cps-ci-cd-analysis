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

        original_metrics = original_analysis.get("size_metrics", {})
        fixed_metrics = fixed_analysis.get("size_metrics", {})
        improvements = self._improvement(original_metrics, fixed_metrics)

        return {
            "success": True,
            "original_metrics": original_metrics,
            "fixed_metrics": fixed_metrics,
            "improvements": improvements,
            "fixed_analysis": fixed_analysis,
        }

    def _improvement(self, original: Dict[str, float], fixed: Dict[str, float]) -> Dict[str, Any]:
        wasted_before = float(original.get("estimated_wasted_space_kb", 0) or 0)
        wasted_after = float(fixed.get("estimated_wasted_space_kb", 0) or 0)
        return {
            "wasted_space_delta_kb": round(wasted_after - wasted_before, 2),
        }

    def print_comparison_report(self, validation_results: Dict[str, Any]) -> None:
        print("\n" + "=" * 60)
        print("SIZE VALIDATION REPORT")
        print("=" * 60)
        original = validation_results.get("original_metrics", {})
        fixed = validation_results.get("fixed_metrics", {})
        improvements = validation_results.get("improvements", {})
        print(f"Original Estimated Waste (kB): {original.get('estimated_wasted_space_kb', 0):.2f}")
        print(f"Fixed Estimated Waste (kB): {fixed.get('estimated_wasted_space_kb', 0):.2f}")
        print(f"Wasted Space Delta (kB): {improvements.get('wasted_space_delta_kb', 0):.2f}")
        print("\n" + "=" * 60 + "\n")
