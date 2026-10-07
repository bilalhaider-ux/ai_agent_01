"""Pydantic schemas and contracts for all workflow stages."""

from typing import List, Dict, Any, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs: Any):
            annotations = {}
            for cls in reversed(self.__class__.__mro__):
                annotations.update(getattr(cls, "__annotations__", {}))
                for k, v in getattr(cls, "__dict__", {}).items():
                    if not k.startswith("_") and not callable(v):
                        if isinstance(v, list):
                            setattr(self, k, list(v))
                        elif isinstance(v, dict):
                            setattr(self, k, dict(v))
                        else:
                            setattr(self, k, v)
            for k, v in kwargs.items():
                expected_type = annotations.get(k)
                if isinstance(expected_type, type) and issubclass(expected_type, BaseModel) and isinstance(v, dict):
                    v = expected_type(**v)
                setattr(self, k, v)

        def model_dump(self) -> dict[str, Any]:
            def _dump(item: Any) -> Any:
                if hasattr(item, "model_dump"):
                    return item.model_dump()
                elif isinstance(item, list):
                    return [_dump(x) for x in item]
                elif isinstance(item, dict):
                    return {k: _dump(val) for k, val in item.items()}
                return item

            res = {}
            for k, v in self.__dict__.items():
                res[k] = _dump(v)
            return res

        def dict(self) -> dict[str, Any]:
            return self.model_dump()

    def Field(*args: Any, **kwargs: Any) -> Any:
        default = kwargs.get("default", ...)
        default_factory = kwargs.get("default_factory")
        if default_factory is not None:
            return default_factory()
        return default if default is not ... else None


class DatasetMinifiedContext(BaseModel):
    """Stage 1: Context Minification Output Contract."""
    row_count: int = Field(description="Total number of rows in the dataset")
    column_count: int = Field(description="Total number of columns")
    columns: List[str] = Field(description="List of column names")
    dtypes: Dict[str, str] = Field(description="Mapping of column name to Polars DataType string")
    null_counts: Dict[str, int] = Field(description="Count of null values per column")
    sample_markdown: str = Field(description="Markdown preview of the first 3-5 rows")
    summary_stats_markdown: str = Field(description="Markdown summary statistics for numerical columns")
    duplicate_row_count: int = Field(default=0, description="Number of duplicate rows")


class AnalyticalPlan(BaseModel):
    """Compatibility contract for the deterministic EDA phase plan."""
    primary_intent: str = Field(
        description="Optional analysis focus retained for API compatibility"
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
    chart_details: List[Dict[str, Any]] = Field(default_factory=list, description="Structured chart descriptors with title, type, and image")
    error_message: Optional[str] = Field(default=None, description="Formatted error description if failed")


class OutputSynthesis(BaseModel):
    """Compatibility contract for the final EDA report envelope."""
    executive_summary: str = Field(description="High-level EDA completion summary")
    statistical_insights: List[str] = Field(description="Verified numerical and statistical insights")
    answers_to_query: str = Field(description="Optional response to the analysis focus")
    recommended_actions: List[str] = Field(description="Evidence-backed EDA next actions")
    full_markdown_report: str = Field(description="Formatted EDA markdown artifact")


class DataHealthSubScores(BaseModel):
    completeness: float = Field(ge=0.0, le=100.0, description="Cell completeness score (0-100)")
    uniqueness: float = Field(ge=0.0, le=100.0, description="Record uniqueness score (0-100)")
    outlier_control: float = Field(ge=0.0, le=100.0, description="Outlier boundary control score (0-100)")
    type_consistency: float = Field(ge=0.0, le=100.0, description="Type validity and non-constant feature score (0-100)")


class DataHealthScore(BaseModel):
    score: float = Field(ge=0.0, le=100.0, description="Deterministic overall Data Health Score (0-100)")
    grade: str = Field(description="Rating grade: Excellent, Good, Moderate, or Critical")
    rating_description: str = Field(description="Executive interpretation of the score")
    sub_scores: DataHealthSubScores = Field(description="Component scores across four data dimensions")
    total_cells: int = Field(default=0, description="Total matrix cells (rows * columns)")
    total_nulls: int = Field(default=0, description="Count of missing/null values")
    duplicate_rows: int = Field(default=0, description="Count of duplicate rows")
    total_outliers: int = Field(default=0, description="Count of IQR outliers")
    zero_variance_columns: List[str] = Field(default_factory=list, description="Zero-variance feature names")


class ParetoAnalysisResult(BaseModel):
    applicable: bool = Field(description="Whether Pareto concentration was applicable")
    column: Optional[str] = Field(default=None, description="Volume/financial candidate feature analyzed")
    is_pareto: bool = Field(default=False, description="True if top 20% records account for >= 60% of total volume")
    top_20_pct_volume_share: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Percentage of total volume held by top 20% records")
    pct_records_generating_80_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Percentage of records generating 80% volume")
    records_generating_80_pct: Optional[int] = Field(default=None, description="Number of records generating 80% volume")
    total_records_evaluated: Optional[int] = Field(default=None, description="Total positive records analyzed")
    total_volume: Optional[float] = Field(default=None, description="Total aggregated feature volume")
    summary: Optional[str] = Field(default=None, description="Executive narrative of Pareto finding")
    reason: Optional[str] = Field(default=None, description="Reason if not applicable")


class MissingnessAlert(BaseModel):
    column: str = Field(description="Feature with missing data")
    missing_count: int = Field(description="Count of missing values")
    missing_pct: float = Field(ge=0.0, le=100.0, description="Percentage of missing values (0-100)")
    severity: str = Field(description="Severity tier: critical, high, medium, low")
    recommended_strategy: str = Field(description="Recommended imputation or remediation strategy")


class MLReadinessWarnings(BaseModel):
    status: str = Field(description="Readiness status: ready or warnings_detected")
    multicollinearity_flags: List[Dict[str, Any]] = Field(default_factory=list, description="Pairs with |r| > 0.85")
    zero_variance_columns: List[Dict[str, Any]] = Field(default_factory=list, description="Zero-variance or single-value features")
    high_cardinality_columns: List[Dict[str, Any]] = Field(default_factory=list, description="Features with >50 unique values or >0.5 ratio")
    candidate_targets: List[Dict[str, Any]] = Field(default_factory=list, description="Candidate target features identified by heuristics")


class BusinessInsights(BaseModel):
    pareto_analysis: ParetoAnalysisResult
    missingness_alerts: List[MissingnessAlert] = Field(default_factory=list)
    ml_readiness: MLReadinessWarnings

