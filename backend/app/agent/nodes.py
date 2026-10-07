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
        chart_details=artifacts.get("chart_details", []),
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
    """Create a grounded EDA synthesis with summary, insights, query context, and recommendations."""
    artifacts = state.get("eda_artifacts", {})
    non_graphical = artifacts.get("non_graphical", {})
    query = state.get("query", "").strip() or "Comprehensive exploratory data analysis"
    metrics = {"exploratory_data_analysis": non_graphical}

    from ..services.report_service import build_strategic_recommendations
    recommendations = build_strategic_recommendations(metrics)
    recommended_action_strings = [
        f"{r['title']}: {r['recommended_action']} ({r['data_justification']})"
        for r in recommendations
    ]

    row_count = non_graphical.get("row_count", 0)
    col_count = non_graphical.get("column_count", 0)
    num_cols = len(non_graphical.get("numeric_summary", {}))
    cat_cols = len(non_graphical.get("categorical_summary", {}))
    dup_rows = non_graphical.get("duplicate_row_count", 0)
    health = non_graphical.get("data_health", {})
    health_score = non_graphical.get("data_health_score", health.get("score"))
    business_insights = non_graphical.get("business_insights", {})
    pareto = business_insights.get("pareto_analysis", {})
    ml_readiness = business_insights.get("ml_readiness", {})

    insights = []
    if row_count:
        health_note = f" Data Health Score: {health_score}/100 ({health.get('grade', 'Reviewed')})." if health_score is not None else ""
        insights.append(f"Analyzed {row_count:,} records across {col_count} columns ({num_cols} numerical, {cat_cols} categorical).{health_note}")
    if dup_rows:
        insights.append(f"Identified {dup_rows:,} duplicate rows requiring review.")
    else:
        insights.append("Zero duplicate rows detected.")

    if pareto.get("applicable"):
        insights.append(f"Pareto concentration: {pareto.get('summary')}")

    missing_alerts = business_insights.get("missingness_alerts", [])
    severe_missing = [a for a in missing_alerts if a.get("severity") in {"critical", "high"}]
    if severe_missing:
        target = severe_missing[0]
        insights.append(f"High-risk missingness alert: `{target['column']}` exhibits {target['missing_pct']}% null values ({target['missing_count']:,} rows).")

    if ml_readiness.get("multicollinearity_flags"):
        collinear_pairs = [f"{f['feature_1']} & {f['feature_2']} (r={f['pearson_r']})" for f in ml_readiness["multicollinearity_flags"][:2]]
        insights.append(f"Multicollinearity warning (|r| > 0.85): {', '.join(collinear_pairs)}.")

    if ml_readiness.get("zero_variance_columns"):
        zero_cols = [f"`{f['column']}`" for f in ml_readiness["zero_variance_columns"][:3]]
        insights.append(f"Zero-variance features detected: {', '.join(zero_cols)} (uninformative constant signals).")

    strongest_rel = non_graphical.get("multivariate", {}).get("strongest_numeric_relationships", [])
    if strongest_rel:
        top_pair = strongest_rel[0]
        cols = top_pair.get("columns", ["feature_1", "feature_2"])
        r_val = top_pair.get("pearson_r")
        r_str = f"{r_val:.3f}" if isinstance(r_val, (int, float)) else str(r_val)
        insights.append(f"Strongest numeric correlation: {cols[0]} & {cols[1]} (Pearson r = {r_str}).")

    stat_tests = non_graphical.get("statistical_tests", {}).get("categorical_numeric_tests", [])
    sig_tests = [t for t in stat_tests if t.get("significant_at_0_05")]
    if sig_tests:
        t = sig_tests[0]
        p_val = t.get("p_value")
        p_str = f"{p_val:.4f}" if isinstance(p_val, (int, float)) else str(p_val)
        insights.append(f"Statistically significant difference ({t.get('test')}): {t.get('numeric')} grouped by {t.get('categorical')} (p = {p_str}).")

    exec_summary = f"Exploratory data analysis of {row_count:,} rows and {col_count} features completed. "
    if health_score is not None:
        exec_summary += f"Dataset earned an overall Data Health Score of {health_score}/100 ({health.get('grade', 'Reviewed')}). "
    exec_summary += "Quality profiling, distribution checks, correlation analysis, and statistical hypothesis testing verified."

    return {
        "synthesis": {
            "executive_summary": exec_summary,
            "statistical_insights": insights,
            "answers_to_query": query,
            "recommended_actions": recommended_action_strings,
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
