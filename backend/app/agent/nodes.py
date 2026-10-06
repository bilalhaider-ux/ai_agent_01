"""Deterministic nodes for the comprehensive exploratory data analysis workflow."""

import re
from typing import Any, Dict

from .contracts import AnalyticalPlan, ExecutionResult
from .eda import run_eda
from .grounding import build_data_quality_report
from .minifier import minify_dataset
from .state import AgentState


def _clean_code_fences(raw_code: Any) -> str:
    """Keep compatibility with callers that normalize provider code responses."""
    if isinstance(raw_code, list):
        text = "\n".join(
            item if isinstance(item, str) else str(item.get("text", item))
            for item in raw_code
        )
    else:
        text = raw_code if isinstance(raw_code, str) else str(raw_code)
    match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", text)
    return match.group(1).strip() if match else text.strip()


def stage1_context_minification(state: AgentState) -> Dict[str, Any]:
    """Profile the dataset and create both summary and visualization artifacts."""
    dataset_path = state["dataset_path"]
    context = minify_dataset(dataset_path)
    return {
        "minified_context": context.model_dump(),
        "data_quality": build_data_quality_report(context.model_dump()),
        "eda_artifacts": run_eda(dataset_path),
        "retry_count": state.get("retry_count", 0),
        "status": "minification_complete",
    }


def stage2_intent_and_plan(state: AgentState) -> Dict[str, Any]:
    """Define the fixed EDA contract without an LLM or user-query interpretation."""
    return {
        "plan": AnalyticalPlan(
            primary_intent="Comprehensive exploratory data analysis",
            data_transformations=[
                "Compute non-graphical statistical summaries",
                "Summarize missingness, duplicates, cardinality, skewness, kurtosis, and IQR outliers",
                "Compute Pearson correlations where numeric data supports them",
                "Generate distributions, box plots, categorical frequencies, and numeric relationships",
                "Detect typed date/time columns for future temporal analysis",
            ],
        ).model_dump(),
        "status": "planning_complete",
    }


def stage3_sandboxed_code_generation(state: AgentState) -> Dict[str, Any]:
    """No generated code is required for deterministic EDA."""
    return {"generated_code": "", "status": "code_generation_skipped"}


def stage4_isolated_execution(state: AgentState) -> Dict[str, Any]:
    """Expose deterministic EDA artifacts through the existing execution contract."""
    artifacts = state["eda_artifacts"]
    result = ExecutionResult(
        success=True,
        metrics={"exploratory_data_analysis": artifacts["non_graphical"]},
        base64_charts=artifacts["charts"],
    )
    return {"execution_result": result.model_dump(), "status": "execution_finished"}


def stage5_self_correction(state: AgentState) -> Dict[str, Any]:
    """Retained for graph compatibility; deterministic EDA has no retry path."""
    return {
        "retry_count": state.get("retry_count", 0) + 1,
        "error_traceback": state.get("execution_result", {}).get("error_message", ""),
        "status": "self_correction_triggered",
    }


def stage6_output_synthesis(state: AgentState) -> Dict[str, Any]:
    """Create a minimal EDA-only synthesis without narrative recommendations."""
    return {
        "synthesis": {
            "executive_summary": "Comprehensive exploratory data analysis completed.",
            "statistical_insights": [],
            "answers_to_query": "",
            "recommended_actions": [],
            "full_markdown_report": "",
        },
        "status": "completed",
    }


def fatal_execution_error_node(state: AgentState) -> Dict[str, Any]:
    """Report an unexpected terminal workflow error."""
    return {
        "fatal_error": "Exploratory data analysis failed.",
        "status": "fatal_error",
    }
