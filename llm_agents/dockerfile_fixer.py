from typing import Any, Dict, Optional


class DockerfileFixer:
    """Fixes Dockerfiles by applying size-focused LLM recommendations."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        try:
            from .dockerfile_llm_analyzer import DockerfileAnalyzer
        except ImportError:
            from dockerfile_llm_analyzer import DockerfileAnalyzer

        self.analyzer = DockerfileAnalyzer(api_key=api_key, model=model)
        self.api_key = self.analyzer.api_key
        self.model = self.analyzer.model

    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return self.analyzer._call_llm(prompt, system_prompt)

    def fix_dockerfile(self, original_dockerfile: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        if not original_dockerfile.strip():
            return {"success": False, "error": "Empty Dockerfile provided", "fixed_dockerfile": original_dockerfile}

        llm_analysis = analysis_results.get("llm_analysis", {}) if analysis_results else {}
        if not llm_analysis.get("success"):
            return {
                "success": False,
                "error": llm_analysis.get("error", "Missing analysis results"),
                "fixed_dockerfile": original_dockerfile,
            }

        llm_data = llm_analysis.get("data", {})
        findings = llm_data.get("size_findings", [])
        recommendations = llm_data.get("size_recommendations", [])

        system_prompt = (
            "You are a cautious Dockerfile editor. Apply only size-reduction fixes that match the findings."
        )
        summary_lines = ["SIZE FINDINGS:"] + [f"- {item}" for item in findings[:10]]
        summary_lines.append("SIZE RECOMMENDATIONS:")
        summary_lines += [f"- {item}" for item in recommendations[:10]]
        summary = "\n".join(summary_lines)

        user_prompt = f"""Update the Dockerfile to reduce image size following the recommendations below.
Make minimal changes and keep all existing functionality.
Return ONLY the updated Dockerfile (no markdown):

ORIGINAL:
```\n{original_dockerfile}\n```

{summary}
"""

        response = self._call_llm(user_prompt, system_prompt)
        if not response or response.startswith("LLM API error"):
            return {"success": False, "error": response or "LLM failed", "fixed_dockerfile": original_dockerfile}

        return {"success": True, "fixed_dockerfile": response.strip()}
