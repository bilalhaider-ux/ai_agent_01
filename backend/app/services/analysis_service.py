"""Application service that runs and normalizes the existing LangGraph agent."""

import json
import hashlib
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

from app.agent.graph import build_data_agent_graph
from app.agent.grounding import build_grounding_metadata, validate_metric_contract
from .report_service import build_report

_analyses: dict[str, dict[str, Any]] = {}


def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    return _analyses.get(analysis_id)


def run_analysis(dataset_path: Path, query: str, provider: str | None, model: str | None, analysis_id: str | None = None) -> dict[str, Any]:
    analysis_id = analysis_id or str(uuid.uuid4())
    record: dict[str, Any] = {"analysis_id": analysis_id, "status": "running"}
    _analyses[analysis_id] = record
    try:
        final_state = build_data_agent_graph().invoke({"query": query, "dataset_path": str(dataset_path), "provider": provider, "model": model, "retry_count": 0})
        if final_state.get("fatal_error"):
            raise RuntimeError(final_state["fatal_error"])
        synthesis = final_state.get("synthesis", {})
        execution = final_state.get("execution_result", {})
        metrics = execution.get("metrics", {})
        metric_errors = validate_metric_contract(metrics)
        if metric_errors:
            raise ValueError("Metric contract validation failed: " + "; ".join(metric_errors))
        grounding = build_grounding_metadata(
            metrics,
            final_state.get("minified_context", {}),
            final_state.get("data_quality", {}),
            dataset_path,
            query,
            provider or final_state.get("provider"),
            model or final_state.get("model"),
        )
        grounding["analysis_id"] = analysis_id
        grounding["reproducibility"]["generated_code_sha256"] = hashlib.sha256(
            final_state.get("generated_code", "").encode("utf-8")
        ).hexdigest()
        markdown, html_report = build_report(synthesis, execution.get("metrics", {}), execution.get("base64_charts", []))
        record.update({
            "status": "completed",
            "executive_summary": synthesis.get("executive_summary", ""),
            "answers_to_query": synthesis.get("answers_to_query", ""),
            "statistical_insights": synthesis.get("statistical_insights", []),
            "recommended_actions": synthesis.get("recommended_actions", []),
            "metrics": metrics,
            "grounding": grounding,
            "generated_code": final_state.get("generated_code", ""),
            "charts": execution.get("base64_charts", []),
            "markdown_report": markdown,
            "html_report": html_report,
        })
    except Exception as exc:
        message = str(exc)
        is_rate_limited = "429" in message or "rate_limited" in message.lower() or "rate limit" in message.lower()
        record.update({
            "status": "failed",
            "error": {
                "type": "ProviderRateLimitError" if is_rate_limited else type(exc).__name__,
                "message": "Mistral rate limit or quota exceeded. Wait and retry, or check your Mistral plan and usage." if is_rate_limited else message,
            },
        })
    finally:
        shutil.rmtree(dataset_path.parent, ignore_errors=True)
    return record
