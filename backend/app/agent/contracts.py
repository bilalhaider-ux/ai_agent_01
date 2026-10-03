"""Pydantic schemas and contracts for all workflow stages."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DatasetMinifiedContext(BaseModel):
    """Stage 1: Context Minification Output Contract."""
    row_count: int = Field(description="Total number of rows in the dataset")
    column_count: int = Field(description="Total number of columns")
    columns: List[str] = Field(description="List of column names")
    dtypes: Dict[str, str] = Field(description="Mapping of column name to Polars DataType string")
    null_counts: Dict[str, int] = Field(description="Count of null values per column")
    sample_markdown: str = Field(description="Markdown preview of the first 3-5 rows")
    summary_stats_markdown: str = Field(description="Markdown summary statistics for numerical columns")


class AnalyticalPlan(BaseModel):
    """Stage 2: Intent & Plan Contract (Pydantic Structured Plan)."""
    primary_intent: str = Field(
        description="Core question or analytical goal derived from the user query"
    )
    hypotheses: List[str] = Field(
        default_factory=list,
        description="Hypotheses or assumptions to test against the data"
    )
    data_transformations: List[str] = Field(
        default_factory=list,
        description="Required Polars operations (filtering, aggregations, joins, new columns)"
    )
    statistical_methods: List[str] = Field(
        default_factory=list,
        description="SciPy or numerical statistical methods (e.g. Pearson correlation, ANOVA, t-test)"
    )
    visualization_plan: List[str] = Field(
        default_factory=list,
        description="Matplotlib visualizations to produce (types, axes, labels, styling)"
    )
    required_metrics: List[str] = Field(
        default_factory=list,
        description="Specific scalar or tabular metrics to be exported in the output contract"
    )


class ExecutionResult(BaseModel):
    """Stage 4: Isolated Execution Runtime Output Contract."""
    success: bool = Field(description="True if the script executed with returncode 0 and valid JSON")
    stdout: str = Field(default="", description="Captured standard output from the execution")
    stderr: str = Field(default="", description="Captured standard error or traceback")
    return_code: int = Field(default=0, description="Exit code of the child subprocess")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Extracted metrics dictionary")
    base64_charts: List[str] = Field(default_factory=list, description="Base64-encoded PNG image strings")
    error_message: Optional[str] = Field(default=None, description="Formatted error description if failed")


class OutputSynthesis(BaseModel):
    """Stage 6: Output Synthesis Contract."""
    executive_summary: str = Field(description="High-level summary of findings for stakeholders")
    statistical_insights: List[str] = Field(description="Specific numerical and statistical insights")
    answers_to_query: str = Field(description="Direct answers answering the user query")
    recommended_actions: List[str] = Field(description="Actionable business or analytical recommendations")
    full_markdown_report: str = Field(description="Formatted decision-ready markdown artifact")

