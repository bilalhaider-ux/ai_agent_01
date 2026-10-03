"""Decision-safety checks for LLM narratives and computed analytical facts."""

from __future__ import annotations

import math
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


def build_grounding_metadata(metrics: dict[str, Any]) -> dict[str, Any]:
    """Create the contract downstream consumers must use for decisions."""
    _validate_json_value(metrics)
    return {
        "status": "verified_metrics_only",
        "metric_count": len(metrics),
        "authoritative_metrics": metrics,
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