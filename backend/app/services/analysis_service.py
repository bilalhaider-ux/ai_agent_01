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
        from .report_service import build_datasnap_suggestions, build_report, build_strategic_recommendations

        non_graphical = metrics.get("exploratory_data_analysis", {})
        num_summary = non_graphical.get("numeric_summary", {})
        cat_summary = non_graphical.get("categorical_summary", {})
        tests = non_graphical.get("statistical_tests", {})
        cat_num_tests = len(tests.get("categorical_numeric_tests", []))
        cat_cat_tests = len(tests.get("categorical_categorical_tests", []))
        bivariate_pairs = len(non_graphical.get("bivariate", {}).get("numeric_pairs", []))
        real_metric_count = (
            len(num_summary) * 12 +
            len(cat_summary) * 4 +
            cat_num_tests + cat_cat_tests + bivariate_pairs
        )
        if real_metric_count == 0:
            real_metric_count = len(metrics)

        grounding = {
            "status": "eda_only",
            "analysis_id": analysis_id,
            "summary_type": "professional_non_graphical_and_visual_exploratory_data_analysis",
            "metric_count": real_metric_count,
            "data_quality": final_state.get("data_quality", {}),
            "visualization_types": final_state.get("eda_artifacts", {}).get("visualization_types", []),
        }
        markdown, html_report = build_report(synthesis, metrics, execution.get("base64_charts", []))
        record.update({
            "status": "completed",
            "executive_summary": synthesis.get("executive_summary", ""),
            "answers_to_query": synthesis.get("answers_to_query", "") or query,
            "statistical_insights": synthesis.get("statistical_insights", []),
            "recommended_actions": build_strategic_recommendations(metrics),
            "datasnap_suggestions": build_datasnap_suggestions(metrics),
            "metrics": metrics,
            "grounding": grounding,
            "generated_code": final_state.get("generated_code", ""),
            "charts": execution.get("base64_charts", []),
            "chart_details": execution.get("chart_details", []),
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
