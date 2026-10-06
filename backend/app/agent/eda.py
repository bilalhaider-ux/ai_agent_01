"""Dataset-agnostic exploratory data analysis artifacts."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import polars as pl
from scipy import stats


def _read_dataset(path: Path) -> pl.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pl.read_csv(path)
    if suffix == ".tsv":
        return pl.read_csv(path, separator="\t")
    if suffix == ".xlsx":
        return pl.read_excel(path)
    if suffix in {".parquet", ".pq"}:
        return pl.read_parquet(path)
    if suffix == ".json":
        return pl.read_json(path)
    if suffix == ".jsonl":
        return pl.read_ndjson(path)
    raise ValueError(f"Unsupported dataset format: {suffix}")


def _chart_base64() -> str:
    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format="png", dpi=120)
    plt.close()
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _finite(value: Any) -> Any:
    if value is None:
        return None
    value = float(value)
    return value if value == value and abs(value) != float("inf") else None


def _date_columns(df: pl.DataFrame) -> list[str]:
    columns = []
    for name, dtype in df.schema.items():
        if dtype in {pl.Date, pl.Datetime}:
            columns.append(name)
            continue
        if dtype == pl.String:
            values = df.get_column(name).drop_nulls()
            if values.len() and values.str.to_date(strict=False).drop_nulls().len() / values.len() >= 0.8:
                columns.append(name)
    return columns


def _correlations(df: pl.DataFrame, numeric: list[str]) -> dict[str, dict[str, float | None]]:
    if len(numeric) < 2:
        return {}
    values = df.select(numeric).drop_nulls()
    if values.height < 3:
        return {}
    matrix = values.to_pandas().corr(method="pearson")
    return {
        column: {other: _finite(matrix.loc[column, other]) for other in numeric}
        for column in numeric
    }


def _numeric_profile(df: pl.DataFrame, name: str) -> dict[str, Any]:
    values = df.get_column(name).drop_nulls()
    raw = values.to_list()
    q1 = _finite(values.quantile(0.25))
    q3 = _finite(values.quantile(0.75))
    std = _finite(values.std())
    profile = {
        "count": values.len(),
        "missing": df.get_column(name).null_count(),
        "mean": _finite(values.mean()),
        "median": _finite(values.median()),
        "std": std,
        "min": _finite(values.min()),
        "max": _finite(values.max()),
        "quantiles": {"q25": q1, "q75": q3},
        "skewness": _finite(stats.skew(raw, bias=False)) if len(raw) >= 3 else None,
        "kurtosis": _finite(stats.kurtosis(raw, bias=False)) if len(raw) >= 4 else None,
        "zero_count": int(sum(value == 0 for value in raw)),
        "negative_count": int(sum(value < 0 for value in raw)),
    }
    if q1 is not None and q3 is not None and values.len() >= 4:
        iqr = q3 - q1
        profile["iqr"] = iqr
        profile["outlier_count_iqr"] = int(
            ((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum()
        )
    else:
        profile["iqr"] = None
        profile["outlier_count_iqr"] = 0
    return profile


def run_eda(dataset_path: str | Path) -> dict[str, Any]:
    """Compute professional, dataset-agnostic descriptive EDA artifacts."""
    df = _read_dataset(Path(dataset_path))
    numeric = [name for name, dtype in df.schema.items() if dtype.is_numeric()]
    categorical = [name for name, dtype in df.schema.items() if not dtype.is_numeric()]
    dates = _date_columns(df)

    numeric_summary = {name: _numeric_profile(df, name) for name in numeric}

    categorical_summary: dict[str, Any] = {}
    for name in categorical:
        values = df.get_column(name).drop_nulls()
        categorical_summary[name] = {
            "missing": df.get_column(name).null_count(),
            "unique": values.n_unique(),
            "cardinality_ratio": round(values.n_unique() / values.len(), 6) if values.len() else None,
            "top_values": [
                {"value": str(row[0]), "count": int(row[1])}
                for row in (
                    df.group_by(name, maintain_order=True)
                    .agg(pl.len().alias("count"))
                    .sort("count", descending=True)
                    .head(10)
                    .iter_rows()
                )
            ],
        }

    charts: list[str] = []
    chart_types: list[str] = []
    for name in numeric[:6]:
        values = df.get_column(name).drop_nulls().to_list()
        if values:
            plt.figure(figsize=(7, 4))
            plt.hist(values, bins=min(20, max(5, len(set(values)))), color="#4f46e5", alpha=0.85)
            plt.title(f"Distribution of {name}")
            plt.xlabel(name)
            plt.ylabel("Frequency")
            charts.append(_chart_base64())
            chart_types.append(f"Histogram: {name}")
            plt.figure(figsize=(7, 4))
            boxplot_options = {
                "patch_artist": True,
                "boxprops": {"facecolor": "#c7d2fe"},
            }
            try:
                plt.boxplot(values, orientation="horizontal", **boxplot_options)
            except TypeError:
                # Older Matplotlib releases use ``vert`` instead of
                # ``orientation`` and may also reject newer label arguments.
                plt.boxplot(values, vert=False, **boxplot_options)
            plt.title(f"Box plot of {name}")
            plt.xlabel(name)
            charts.append(_chart_base64())
            chart_types.append(f"Box plot: {name}")
    for name in categorical[:6]:
        counts = (
            df.group_by(name, maintain_order=True)
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
            .head(10)
        )
        if counts.height:
            plt.figure(figsize=(7, 4))
            plt.bar([str(value) for value in counts[name].to_list()], counts["count"].to_list(), color="#0f9d6b")
            plt.title(f"Top categories in {name}")
            plt.xlabel(name)
            plt.ylabel("Count")
            plt.xticks(rotation=35, ha="right")
            charts.append(_chart_base64())
            chart_types.append(f"Category frequency: {name}")

    if len(numeric) >= 2:
        first, second = numeric[:2]
        pairs = df.select([first, second]).drop_nulls()
        if pairs.height:
            plt.figure(figsize=(7, 4))
            plt.scatter(pairs[first].to_list(), pairs[second].to_list(), alpha=0.7, color="#d97706")
            plt.title(f"Relationship between {first} and {second}")
            plt.xlabel(first)
            plt.ylabel(second)
            charts.append(_chart_base64())
            chart_types.append(f"Scatter plot: {first} vs {second}")

    quality_flags = []
    if df.height == 0:
        quality_flags.append("empty_dataset")
    if any(value for value in {name: df.get_column(name).null_count() for name in df.columns}.values()):
        quality_flags.append("missing_values_present")
    if df.is_duplicated().sum():
        quality_flags.append("duplicate_rows_present")
    if any(item["outlier_count_iqr"] for item in numeric_summary.values()):
        quality_flags.append("iqr_outliers_present")

    return {
        "summary_type": "professional_non_graphical_and_visual_exploratory_data_analysis",
        "non_graphical": {
            "row_count": df.height,
            "column_count": df.width,
            "columns": df.columns,
            "dtypes": {name: str(dtype) for name, dtype in df.schema.items()},
            "missing_counts": {name: int(df.get_column(name).null_count()) for name in df.columns},
            "duplicate_row_count": int(df.is_duplicated().sum()),
            "numeric_summary": numeric_summary,
            "categorical_summary": categorical_summary,
            "outlier_counts_iqr": {
                name: profile["outlier_count_iqr"]
                for name, profile in numeric_summary.items()
            },
            "correlation_matrix_pearson": _correlations(df, numeric),
            "date_columns": dates,
            "quality_flags": quality_flags,
        },
        "visualization_count": len(charts),
        "visualization_types": chart_types,
        "charts": charts,
    }
