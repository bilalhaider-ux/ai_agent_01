"""Application service that runs and normalizes the existing LangGraph agent."""

import json
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

from app.agent.graph import build_data_agent_graph
from app.agent.grounding import build_grounding_metadata
from .report_service import build_report

_analyses: dict[str, dict[str, Any]] = {}


def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    return _analyses.get(analysis_id)


def run_analysis(dataset_path: Path, query: str, provider: str | None, model: str | None) -> dict[str, Any]:
    analysis_id = str(uuid.uuid4())
    record: dict[str, Any] = {"analysis_id": analysis_id, "status": "running"}
    _analyses[analysis_id] = record
    try:
        final_state = build_data_agent_graph().invoke({"query": query, "dataset_path": str(dataset_path), "provider": provider, "model": model, "retry_count": 0})
        if final_state.get("fatal_error"):
            raise RuntimeError(final_state["fatal_error"])
        synthesis = final_state.get("synthesis", {})
        execution = final_state.get("execution_result", {})
        grounding = build_grounding_metadata(execution.get("metrics", {}))
        markdown, html_report = build_report(synthesis, execution.get("metrics", {}), execution.get("base64_charts", []))
        record.update({
            "status": "completed",
            "executive_summary": synthesis.get("executive_summary", ""),
            "answers_to_query": synthesis.get("answers_to_query", ""),
            "statistical_insights": synthesis.get("statistical_insights", []),
            "recommended_actions": synthesis.get("recommended_actions", []),
            "metrics": execution.get("metrics", {}),
            "grounding": grounding,
            "charts": execution.get("base64_charts", []),
            "markdown_report": markdown,
            "html_report": html_report,
        })
    except Exception as exc:
        record.update({"status": "failed", "error": {"type": type(exc).__name__, "message": str(exc)}})
    finally:
        shutil.rmtree(dataset_path.parent, ignore_errors=True)
    return record