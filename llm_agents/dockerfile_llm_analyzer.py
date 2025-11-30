import json
import os
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass


class DockerfileAnalyzer:
    """LLM-backed analyzer focused solely on image size opportunities."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY or pass api_key.")

        if not model:
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai is required. Install with: pip install google-generativeai")

        self.api_key = api_key
        self.model = model
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model)

    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        full_prompt = prompt if not system_prompt else f"{system_prompt}\n\n{prompt}"
        try:
            response = self.client.generate_content(
                full_prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 2000},
            )
            if hasattr(response, "text") and response.text:
                return response.text.strip()
            return ""
        except Exception as exc:  # pragma: no cover - API failure handling
            return f"LLM API error: {exc}"

    def analyze_dockerfile(self, dockerfile_path: str) -> Dict[str, Any]:
        try:
            with open(dockerfile_path, "r", encoding="utf-8") as handle:
                dockerfile_content = handle.read()
        except FileNotFoundError:
            return {"error": f"Dockerfile not found: {dockerfile_path}", "size_metrics": {}}

        system_prompt = (
            "You are a Docker image size expert. Identify only size-related inefficiencies and wasted space."
        )
        user_prompt = f"""Review this Dockerfile and return JSON:
{{
  "size_findings": ["list concrete causes of size bloat"],
  "size_recommendations": ["actionable steps to reduce size"],
  "estimated_wasted_space_kb": <number>
}}
Do not mention security or performance. Only talk about image size.
Dockerfile:\n```\n{dockerfile_content}\n```"""

        raw_response = self._call_llm(user_prompt, system_prompt)
        if raw_response.startswith("LLM API error"):
            return {
                "dockerfile_path": dockerfile_path,
                "llm_analysis": {"success": False, "error": raw_response, "data": {}},
                "size_metrics": {"estimated_wasted_space_kb": 0},
            }

        cleaned = raw_response.strip()
        if "```" in cleaned:
            start = cleaned.find("```")
            end = cleaned.rfind("```")
            cleaned = cleaned[start + 3 : end].strip() if end > start else cleaned

        try:
            llm_data = json.loads(cleaned)
        except json.JSONDecodeError:
            llm_data = {}

        wasted_kb = llm_data.get("estimated_wasted_space_kb", 0) or 0
        try:
            wasted_kb = float(wasted_kb)
        except (TypeError, ValueError):
            wasted_kb = 0.0

        metrics = {"estimated_wasted_space_kb": round(wasted_kb, 2)}

        analysis = {
            "success": True,
            "data": {
                "size_findings": llm_data.get("size_findings", []),
                "size_recommendations": llm_data.get("size_recommendations", []),
                "estimated_wasted_space_kb": wasted_kb,
            },
            "raw_response": raw_response,
        }

        print(f"  [LLM Size Analysis] wasted_kb={metrics['estimated_wasted_space_kb']}")

        return {"dockerfile_path": dockerfile_path, "llm_analysis": analysis, "size_metrics": metrics}

    def print_analysis_report(self, analysis_result: Dict[str, Any]) -> None:
        if "error" in analysis_result:
            print(f"  ERROR: {analysis_result['error']}")
            return

        metrics = analysis_result.get("size_metrics", {})
        llm_analysis = analysis_result.get("llm_analysis", {})
        llm_data = llm_analysis.get("data", {}) if llm_analysis else {}

        print("\n" + "=" * 60)
        print("DOCKERFILE SIZE ANALYSIS")
        print("=" * 60)
        print(f"Estimated Wasted Space: {metrics.get('estimated_wasted_space_kb', 0):.2f} kB")

        findings = llm_data.get("size_findings", [])
        if findings:
            print("\nSize Findings:")
            for item in findings:
                print(f"  - {item}")

        recommendations = llm_data.get("size_recommendations", [])
        if recommendations:
            print("\nSize Recommendations:")
            for rec in recommendations:
                print(f"  * {rec}")

        print("\n" + "=" * 60 + "\n")


def find_dockerfiles(repo_path: str) -> List[str]:
    matches: List[str] = []
    for root, _dirs, files in os.walk(repo_path):
        for name in files:
            lname = name.lower()
            if lname == "dockerfile" or lname.startswith("dockerfile."):
                matches.append(os.path.join(root, name))
    return matches
