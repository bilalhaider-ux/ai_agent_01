"""Application service that runs and normalizes the existing LangGraph agent."""

import shutil
import uuid
from pathlib import Path
from typing import Any

from app.agent.graph import build_data_agent_graph
from app.agent.grounding import validate_metric_contract
from .report_service import build_datasnap_suggestions, build_report

def get_analysis(analysis_id: str) -> dict[str, Any] | None:
    from .job_service import job_store

    return job_store.get(analysis_id)


def run_analysis(dataset_path: Path, query: str, provider: str | None, model: str | None, analysis_id: str | None = None) -> dict[str, Any]:
    analysis_id = analysis_id or str(uuid.uuid4())
    record: dict[str, Any] = {"analysis_id": analysis_id, "status": "running"}
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
        grounding = {
            "status": "eda_only",
            "analysis_id": analysis_id,
            "summary_type": "professional_non_graphical_and_visual_exploratory_data_analysis",
            "metric_count": len(metrics),
            "data_quality": final_state.get("data_quality", {}),
        }
        markdown, html_report = build_report(synthesis, metrics, execution.get("base64_charts", []))
        record.update({
            "status": "completed",
            "executive_summary": synthesis.get("executive_summary", ""),
            "answers_to_query": synthesis.get("answers_to_query", ""),
            "statistical_insights": synthesis.get("statistical_insights", []),
            "recommended_actions": synthesis.get("recommended_actions", []),
            "datasnap_suggestions": build_datasnap_suggestions(metrics),
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
                "message": "The configured LLM provider rate limit or quota was exceeded. Wait and retry, or check provider usage." if is_rate_limited else message,
            },
        })
    finally:
        shutil.rmtree(dataset_path.parent, ignore_errors=True)
    return record
