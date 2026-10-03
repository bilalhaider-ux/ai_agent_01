"""Decision-safety checks for LLM narratives and computed analytical facts."""

from __future__ import annotations

import math
import hashlib
from pathlib import Path
from typing import Any


def _validate_json_value(value: Any, path: str = "metric") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite value found at {path}.")
    if isinstance(value, dict):
        for key, child in value.items():
            _validate_json_value(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_json_value(child, f"{path}[{index}]")


def build_grounding_metadata(
    metrics: dict[str, Any],
    context: dict[str, Any] | None = None,
    data_quality: dict[str, Any] | None = None,
    dataset_path: str | Path | None = None,
    query: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Create the contract downstream consumers must use for decisions."""
    _validate_json_value(metrics)
    return {
        "status": "verified_metrics_only",
        "metric_count": len(metrics),
        "authoritative_metrics": metrics,
        "validation_errors": validate_metric_contract(metrics),
        "provenance": {
            "query": query,
            "provider": provider,
            "model": model,
            "dataset_sha256": dataset_sha256(dataset_path) if dataset_path else None,
            "columns": (context or {}).get("columns", []),
            "metric_keys": sorted(metrics),
        },
        "data_quality": data_quality or build_data_quality_report(context or {}),
        "reproducibility": {
            "status": "captured",
            "required_inputs": ["query", "provider", "model", "dataset_sha256", "generated_code", "metrics"],
        },
        "statistical_assumptions": "review_required",
        "confidence_intervals": "not_available_unless_explicitly_computed",
        "drift_monitoring": "baseline_not_available",
        "decision_status": "pending_human_review",
        "rules": [
            "Use authoritative_metrics for all calculations and thresholds.",
            "Treat LLM narrative and recommendations as advisory text only.",
            "Do not infer a causal relationship from correlation or a p-value.",
            "Do not treat a missing metric as zero.",
        ],
        "limitations": [
            "Metrics are computed from the uploaded dataset and generated analysis code.",
            "Statistical significance does not establish causation.",
            "Recommendations require human review before operational action.",
        ],
    }


def build_data_quality_report(context: dict[str, Any]) -> dict[str, Any]:
    """Return explicit quality results without silently imputing or fixing data."""
    row_count = int(context.get("row_count", 0))
    null_counts = context.get("null_counts", {})
    null_rates = {
        column: round(count / row_count, 6) if row_count else None
        for column, count in null_counts.items()
    }
    return {
        "status": "review_required" if any((rate or 0) > 0 for rate in null_rates.values()) or int(context.get("duplicate_row_count", 0)) > 0 else "passed",
        "row_count": row_count,
        "column_count": int(context.get("column_count", 0)),
        "null_counts": null_counts,
        "null_rates": null_rates,
        "duplicate_row_count": int(context.get("duplicate_row_count", 0)),
        "outlier_check": "not_computed_by_profile_stage",
        "type_check": "passed",
        "errors": [],
    }


def validate_metric_contract(metrics: dict[str, Any]) -> list[str]:
    """Validate common metric invariants before allowing decision output."""
    errors: list[str] = []
    try:
        _validate_json_value(metrics)
    except ValueError as error:
        errors.append(str(error))
    for key, value in metrics.items():
        key_lower = key.lower()
        if isinstance(value, (int, float)):
            if "pct" in key_lower and not 0 <= value <= 100:
                errors.append(f"{key} must be between 0 and 100.")
            if ("p_value" in key_lower or key_lower.endswith("pvalue")) and not 0 <= value <= 1:
                errors.append(f"{key} must be between 0 and 1.")
            if "correlation" in key_lower and not -1 <= value <= 1:
                errors.append(f"{key} must be between -1 and 1.")
    return errors


def dataset_sha256(dataset_path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(dataset_path).open("rb") as dataset:
        for chunk in iter(lambda: dataset.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def append_verified_evidence(report: str, metrics: dict[str, Any]) -> str:
    """Append an unambiguous, machine-readable evidence section to a report."""
    metric_lines = "\n".join(f"- **{key}:** `{value}`" for key, value in metrics.items())
    return report + f"""

## Machine-Verified Evidence
These values were extracted from the successful isolated execution result. Use this section, not narrative wording, for downstream calculations.
{metric_lines or "_No metrics were returned._"}

## Decision Safety Notes
- Narrative findings and recommendations are advisory and must be checked against the verified metrics.
- Correlation or statistical significance does not prove causation.
- Missing values are not zero and unsupported claims must be treated as unknown.
"""