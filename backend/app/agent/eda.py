"""Dataset-agnostic exploratory data analysis artifacts."""

from __future__ import annotations

import base64
import io
from collections import defaultdict
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
    values = df.select(numeric).drop_nulls().head(100_000)
    if values.height < 3:
        return {}
    matrix = values.to_pandas().corr(method="pearson")
    return {
        column: {other: _finite(matrix.loc[column, other]) for other in numeric}
        for column in numeric
    }


def _bivariate_analysis(
    df: pl.DataFrame,
    numeric: list[str],
    categorical: list[str],
) -> dict[str, Any]:
    numeric_pairs: list[dict[str, Any]] = []
    # Evaluate up to 15 numeric columns to prevent combinatorial explosion
    eval_numeric = numeric[:15]
    for index, first in enumerate(eval_numeric):
        for second in eval_numeric[index + 1:]:
            values = df.select([first, second]).drop_nulls().head(100_000)
            if values.height < 3:
                continue
            x_raw = values[first].to_list()
            y_raw = values[second].to_list()
            # Filter finite pairs
            pairs = [
                (float(a), float(b))
                for a, b in zip(x_raw, y_raw)
                if _finite(a) is not None and _finite(b) is not None
            ]
            if len(pairs) < 3:
                continue
            x = [p[0] for p in pairs]
            y = [p[1] for p in pairs]
            pearson = None
            spearman = None
            if len(set(x)) > 1 and len(set(y)) > 1:
                try:
                    pearson = stats.pearsonr(x, y)
                except Exception:
                    pearson = None
                try:
                    spearman = stats.spearmanr(x, y)
                except Exception:
                    spearman = None
            numeric_pairs.append({
                "columns": [first, second],
                "count": len(pairs),
                "pearson_r": _finite(pearson.statistic) if pearson else None,
                "pearson_p_value": _finite(pearson.pvalue) if pearson else None,
                "spearman_r": _finite(spearman.statistic) if spearman else None,
                "spearman_p_value": _finite(spearman.pvalue) if spearman else None,
            })

    categorical_numeric: list[dict[str, Any]] = []
    for category in categorical[:8]:
        for measure in numeric[:8]:
            grouped = (
                df.select([category, measure])
                .drop_nulls()
                .group_by(category)
                .agg([
                    pl.len().alias("count"),
                    pl.col(measure).mean().alias("mean"),
                    pl.col(measure).median().alias("median"),
                ])
                .sort("count", descending=True)
                .head(10)
            )
            if grouped.height:
                categorical_numeric.append({
                    "category": category,
                    "numeric": measure,
                    "groups": [
                        {
                            "value": str(row[0]),
                            "count": int(row[1]),
                            "mean": _finite(row[2]),
                            "median": _finite(row[3]),
                        }
                        for row in grouped.iter_rows()
                    ],
                })
    return {
        "numeric_pairs": numeric_pairs,
        "categorical_numeric_groups": categorical_numeric,
    }


def _multivariate_analysis(
    df: pl.DataFrame,
    numeric: list[str],
    categorical: list[str],
) -> dict[str, Any]:
    correlations = _correlations(df, numeric)
    ranked_pairs = []
    for first, values in correlations.items():
        for second, value in values.items():
            if first < second and value is not None:
                ranked_pairs.append({
                    "columns": [first, second],
                    "pearson_r": value,
                    "absolute_r": abs(value),
                })
    ranked_pairs.sort(key=lambda item: item["absolute_r"], reverse=True)
    return {
        "numeric_feature_count": len(numeric),
        "categorical_feature_count": len(categorical),
        "pearson_correlation_matrix": correlations,
        "strongest_numeric_relationships": ranked_pairs[:10],
        "usable_numeric_rows": int(df.select(numeric).drop_nulls().height) if numeric else 0,
    }


def _statistical_tests(
    df: pl.DataFrame,
    numeric: list[str],
    categorical: list[str],
) -> dict[str, Any]:
    """Run bounded, assumption-transparent tests for observed interactions."""
    categorical_numeric: list[dict[str, Any]] = []
    for category in categorical[:8]:
        for measure in numeric[:8]:
            groups: dict[str, list[float]] = defaultdict(list)
            for row in df.select([category, measure]).drop_nulls().iter_rows():
                val = _finite(row[1])
                if val is not None:
                    groups[str(row[0])].append(val)
            usable = [values for values in groups.values() if len(values) >= 2]
            if len(usable) < 2:
                continue
            if len(usable) == 2:
                try:
                    result = stats.ttest_ind(*usable, equal_var=False)
                    test_name = "Welch t-test"
                except Exception:
                    continue
            else:
                try:
                    result = stats.f_oneway(*usable)
                    test_name = "One-way ANOVA"
                except Exception:
                    continue
            p_val = _finite(result.pvalue)
            categorical_numeric.append({
                "categorical": category,
                "numeric": measure,
                "test": test_name,
                "group_count": len(usable),
                "sample_sizes": [len(values) for values in usable],
                "statistic": _finite(result.statistic),
                "p_value": p_val,
                "significant_at_0_05": bool(p_val is not None and p_val < 0.05),
            })

    categorical_pairs: list[dict[str, Any]] = []
    for index, first in enumerate(categorical[:8]):
        for second in categorical[index + 1:8]:
            counts: dict[tuple[str, str], int] = defaultdict(int)
            first_values: set[str] = set()
            second_values: set[str] = set()
            for left, right in df.select([first, second]).drop_nulls().iter_rows():
                left_key, right_key = str(left), str(right)
                counts[(left_key, right_key)] += 1
                first_values.add(left_key)
                second_values.add(right_key)
            if len(first_values) < 2 or len(second_values) < 2:
                continue
            table = [
                [counts[(left, right)] for right in second_values]
                for left in first_values
            ]
            try:
                result = stats.chi2_contingency(table)
                p_val = _finite(result.pvalue)
                categorical_pairs.append({
                    "categorical_columns": [first, second],
                    "test": "Chi-square test of independence",
                    "degrees_of_freedom": int(result.dof),
                    "statistic": _finite(result.statistic),
                    "p_value": p_val,
                    "significant_at_0_05": bool(p_val is not None and p_val < 0.05),
                })
            except Exception:
                continue
    return {
        "categorical_numeric_tests": categorical_numeric,
        "categorical_categorical_tests": categorical_pairs,
    }


def _numeric_profile(df: pl.DataFrame, name: str) -> dict[str, Any]:
    values = df.get_column(name).drop_nulls()
    raw = [v for v in values.to_list() if _finite(v) is not None]
    q1 = _finite(values.quantile(0.25))
    q3 = _finite(values.quantile(0.75))
    std = _finite(values.std())
    zero_count = int((values == 0).sum()) if values.len() else 0
    negative_count = int((values < 0).sum()) if values.len() else 0
    skewness = None
    kurtosis = None
    if len(raw) >= 3:
        try:
            skewness = _finite(stats.skew(raw, bias=False))
        except Exception:
            skewness = None
    if len(raw) >= 4:
        try:
            kurtosis = _finite(stats.kurtosis(raw, bias=False))
        except Exception:
            kurtosis = None

    profile = {
        "count": values.len(),
        "missing": df.get_column(name).null_count(),
        "mean": _finite(values.mean()),
        "median": _finite(values.median()),
        "std": std,
        "variance": _finite(values.var()),
        "min": _finite(values.min()),
        "max": _finite(values.max()),
        "quantiles": {"q25": q1, "q75": q3},
        "skewness": skewness,
        "kurtosis": kurtosis,
        "zero_count": zero_count,
        "negative_count": negative_count,
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
        top_rows = (
            df.filter(pl.col(name).is_not_null())
            .group_by(name, maintain_order=True)
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
            .head(10)
            .iter_rows()
        )
        categorical_summary[name] = {
            "missing": df.get_column(name).null_count(),
            "unique": values.n_unique(),
            "cardinality_ratio": round(values.n_unique() / values.len(), 6) if values.len() else None,
            "top_values": [
                {"value": str(row[0]), "count": int(row[1])}
                for row in top_rows
            ],
        }

    bivariate = _bivariate_analysis(df, numeric, categorical)
    multivariate = _multivariate_analysis(df, numeric, categorical)
    statistical_tests = _statistical_tests(df, numeric, categorical)
    charts: list[str] = []
    chart_types: list[str] = []
    chart_details: list[dict[str, Any]] = []

    for name in numeric[:6]:
        values = [v for v in df.get_column(name).drop_nulls().head(20_000).to_list() if _finite(v) is not None]
        if values:
            try:
                plt.figure(figsize=(7, 4))
                plt.hist(values, bins=min(20, max(5, len(set(values)))), color="#4f46e5", alpha=0.85)
                plt.title(f"Distribution of {name}")
                plt.xlabel(name)
                plt.ylabel("Frequency")
                b64 = _chart_base64()
                charts.append(b64)
                t = f"Histogram: {name}"
                chart_types.append(t)
                chart_details.append({"title": t, "type": "histogram", "feature": name, "image": b64})
            finally:
                plt.close("all")

            try:
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
                b64 = _chart_base64()
                charts.append(b64)
                t = f"Box plot: {name}"
                chart_types.append(t)
                chart_details.append({"title": t, "type": "box_plot", "feature": name, "image": b64})
            finally:
                plt.close("all")

    for name in categorical[:6]:
        counts = (
            df.filter(pl.col(name).is_not_null())
            .group_by(name, maintain_order=True)
            .agg(pl.len().alias("count"))
            .sort("count", descending=True)
            .head(10)
        )
        if counts.height:
            try:
                plt.figure(figsize=(7, 4))
                plt.bar([str(value) for value in counts[name].to_list()], counts["count"].to_list(), color="#0f9d6b")
                plt.title(f"Top categories in {name}")
                plt.xlabel(name)
                plt.ylabel("Count")
                plt.xticks(rotation=35, ha="right")
                b64 = _chart_base64()
                charts.append(b64)
                t = f"Category frequency: {name}"
                chart_types.append(t)
                chart_details.append({"title": t, "type": "bar_chart", "feature": name, "image": b64})
            finally:
                plt.close("all")

    for first, second in [
        pair["columns"] for pair in bivariate["numeric_pairs"][:3]
    ]:
        pairs = df.select([first, second]).drop_nulls()
        if pairs.height:
            pairs = pairs.head(20_000)
            x_vals = [v for v in pairs[first].to_list() if _finite(v) is not None]
            y_vals = [v for v in pairs[second].to_list() if _finite(v) is not None]
            min_len = min(len(x_vals), len(y_vals))
            if min_len >= 3:
                try:
                    plt.figure(figsize=(7, 4))
                    plt.scatter(x_vals[:min_len], y_vals[:min_len], alpha=0.7, color="#d97706")
                    plt.title(f"Relationship between {first} and {second}")
                    plt.xlabel(first)
                    plt.ylabel(second)
                    b64 = _chart_base64()
                    charts.append(b64)
                    t = f"Scatter plot: {first} vs {second}"
                    chart_types.append(t)
                    chart_details.append({"title": t, "type": "scatter_plot", "feature": f"{first} vs {second}", "image": b64})
                finally:
                    plt.close("all")

    if len(numeric) >= 2 and multivariate["pearson_correlation_matrix"]:
        try:
            usable_df = df.select(numeric).drop_nulls().head(100_000)
            if usable_df.height >= 3:
                matrix = usable_df.to_pandas().corr(method="pearson").fillna(0)
                plt.figure(figsize=(max(6, len(numeric) * 0.7), max(5, len(numeric) * 0.6)))
                image = plt.imshow(matrix.to_numpy(), cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
                plt.colorbar(image, label="Pearson r")
                plt.xticks(range(len(numeric)), numeric, rotation=45, ha="right")
                plt.yticks(range(len(numeric)), numeric)
                plt.title("Multivariate Pearson correlation matrix")
                b64 = _chart_base64()
                charts.append(b64)
                t = "Correlation heatmap: numeric features"
                chart_types.append(t)
                chart_details.append({"title": t, "type": "heatmap", "feature": "numeric_correlations", "image": b64})
        finally:
            plt.close("all")

    duplicate_row_count = int(df.is_duplicated().sum()) if df.height else 0
    data_health = _calculate_data_health_score(
        df, numeric, categorical, numeric_summary, categorical_summary, duplicate_row_count
    )
    pareto = _pareto_analysis(df, numeric)
    missing_alerts = _missingness_alerts(df)
    ml_readiness = _ml_readiness_warnings(
        df, numeric, categorical, multivariate.get("pearson_correlation_matrix", {}), numeric_summary, categorical_summary
    )

    quality_flags = []
    if df.height == 0:
        quality_flags.append("empty_dataset")
    if any(value for value in {name: df.get_column(name).null_count() for name in df.columns}.values()):
        quality_flags.append("missing_values_present")
    if duplicate_row_count:
        quality_flags.append("duplicate_rows_present")
    if any(item["outlier_count_iqr"] for item in numeric_summary.values()):
        quality_flags.append("iqr_outliers_present")
    if data_health["score"] < 75:
        quality_flags.append(f"data_health_{data_health['grade'].lower()}")
    if ml_readiness.get("multicollinearity_flags"):
        quality_flags.append("multicollinearity_detected")
    if ml_readiness.get("zero_variance_columns"):
        quality_flags.append("zero_variance_features_present")

    return {
        "summary_type": "professional_non_graphical_and_visual_exploratory_data_analysis",
        "non_graphical": {
            "row_count": df.height,
            "column_count": df.width,
            "columns": df.columns,
            "dtypes": {name: str(dtype) for name, dtype in df.schema.items()},
            "data_health": data_health,
            "data_health_score": data_health["score"],
            "business_insights": {
                "pareto_analysis": pareto,
                "missingness_alerts": missing_alerts,
                "ml_readiness": ml_readiness,
            },
            "missing_counts": {name: int(df.get_column(name).null_count()) for name in df.columns},
            "missing_percentages": {
                name: round((df.get_column(name).null_count() / df.height) * 100, 4)
                if df.height else None
                for name in df.columns
            },
            "duplicate_row_count": duplicate_row_count,
            "numeric_summary": numeric_summary,
            "categorical_summary": categorical_summary,
            "univariate": {
                "numeric_profiles": numeric_summary,
                "categorical_profiles": categorical_summary,
                "date_columns": dates,
            },
            "bivariate": bivariate,
            "multivariate": multivariate,
            "statistical_tests": statistical_tests,
            "high_cardinality_categorical_columns": [
                {
                    "column": name,
                    "unique_count": profile["unique"],
                    "cardinality_ratio": profile["cardinality_ratio"],
                }
                for name, profile in categorical_summary.items()
                if profile["unique"] >= 20 or (profile["cardinality_ratio"] or 0) >= 0.5
            ],
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
        "chart_details": chart_details,
    }


def _calculate_data_health_score(
    df: pl.DataFrame,
    numeric: list[str],
    categorical: list[str],
    numeric_summary: dict[str, Any],
    categorical_summary: dict[str, Any],
    duplicate_rows: int,
) -> dict[str, Any]:
    row_count = df.height
    col_count = df.width
    total_cells = row_count * col_count if row_count and col_count else 0

    if row_count == 0:
        return {
            "score": 0.0,
            "grade": "Critical",
            "rating_description": "Dataset is empty (zero records).",
            "sub_scores": {
                "completeness": 0.0,
                "uniqueness": 0.0,
                "outlier_control": 0.0,
                "type_consistency": 0.0,
            },
            "total_cells": 0,
            "total_nulls": 0,
            "duplicate_rows": 0,
            "total_outliers": 0,
            "zero_variance_columns": [],
        }

    total_nulls = sum(int(df.get_column(c).null_count()) for c in df.columns)
    null_rate = total_nulls / total_cells if total_cells else 1.0
    completeness_score = round(max(0.0, min(100.0, (1.0 - null_rate) * 100.0)), 1)

    if row_count == 0:
        uniqueness_score = 0.0
    else:
        dup_rate = duplicate_rows / row_count
        uniqueness_score = round(max(0.0, min(100.0, (1.0 - dup_rate) * 100.0)), 1)

    total_numeric_values = sum(numeric_summary[c].get("count", 0) for c in numeric)
    total_iqr_outliers = sum(numeric_summary[c].get("outlier_count_iqr", 0) for c in numeric)
    if total_numeric_values == 0:
        outlier_score = 100.0
    else:
        outlier_rate = total_iqr_outliers / total_numeric_values
        outlier_score = round(max(0.0, min(100.0, (1.0 - min(1.0, outlier_rate * 2.0)) * 100.0)), 1)

    penalties = 0.0
    zero_var_cols = []
    for c in numeric:
        std = numeric_summary[c].get("std")
        val_min = numeric_summary[c].get("min")
        val_max = numeric_summary[c].get("max")
        if (std == 0.0 or (val_min is not None and val_min == val_max)) and numeric_summary[c].get("count", 0) > 1:
            zero_var_cols.append(c)
            penalties += 15.0
    for c in categorical:
        uniq = categorical_summary[c].get("unique", 0)
        if uniq <= 1 and row_count > 1:
            penalties += 10.0
    if row_count > 0:
        for c in df.columns:
            if df.get_column(c).null_count() == row_count:
                penalties += 20.0
    type_score = round(max(0.0, min(100.0, 100.0 - penalties)), 1)

    overall_score = round(
        completeness_score * 0.30 +
        uniqueness_score * 0.25 +
        outlier_score * 0.25 +
        type_score * 0.20,
        1
    )

    if overall_score >= 90:
        grade = "Excellent"
        rating_description = "High integrity, production & modeling ready"
    elif overall_score >= 75:
        grade = "Good"
        rating_description = "Robust quality with minor remediation recommended"
    elif overall_score >= 50:
        grade = "Moderate"
        rating_description = "Data cleansing & outlier controls required before modeling"
    else:
        grade = "Critical"
        rating_description = "Substantial quality deficits detected; manual remediation required"

    return {
        "score": overall_score,
        "grade": grade,
        "rating_description": rating_description,
        "sub_scores": {
            "completeness": completeness_score,
            "uniqueness": uniqueness_score,
            "outlier_control": outlier_score,
            "type_consistency": type_score,
        },
        "total_cells": total_cells,
        "total_nulls": total_nulls,
        "duplicate_rows": duplicate_rows,
        "total_outliers": total_iqr_outliers,
        "zero_variance_columns": zero_var_cols,
    }


def _pareto_analysis(df: pl.DataFrame, numeric: list[str]) -> dict[str, Any]:
    """Identify 80/20 concentration patterns on financial or volume measures."""
    if df.height < 5 or not numeric:
        return {
            "applicable": False,
            "reason": "Insufficient records or numerical features for concentration analysis."
        }

    priority_keywords = ["revenue", "sales", "price", "amount", "total", "cost", "quantity", "units", "spend", "profit"]
    candidates = []
    for c in numeric:
        c_lower = c.lower()
        score = 0
        for kw in priority_keywords:
            if kw in c_lower:
                score += 10
        s = df.get_column(c).drop_nulls()
        if s.len() > 0 and (s >= 0).sum() / s.len() >= 0.95 and (s.sum() or 0) > 0:
            score += 5
            candidates.append((score, c))

    if not candidates:
        for c in numeric:
            s = df.get_column(c).drop_nulls()
            if s.len() > 0 and (s >= 0).sum() / s.len() >= 0.95 and (s.sum() or 0) > 0:
                candidates.append((1, c))
                break

    if not candidates:
        return {
            "applicable": False,
            "reason": "No positive volume or financial candidate column found."
        }

    # Deterministic sorting by score descending, then column name ascending
    candidates.sort(key=lambda x: (-x[0], x[1]))
    target_col = candidates[0][1]

    sorted_vals = df.select(target_col).drop_nulls().filter(pl.col(target_col) > 0).sort(target_col, descending=True)
    n = sorted_vals.height
    if n < 5:
        return {
            "applicable": False,
            "column": target_col,
            "reason": "Fewer than 5 positive observations."
        }

    total_val = float(sorted_vals[target_col].sum() or 0.0)
    if total_val <= 0:
        return {
            "applicable": False,
            "column": target_col,
            "reason": "Total volume sum is zero."
        }

    cum_series = sorted_vals[target_col].cum_sum()
    target_80 = total_val * 0.80

    rows_for_80 = min(n, int((cum_series < target_80).sum()) + 1)
    pct_rows_for_80 = round(min(100.0, max(0.0, (rows_for_80 / n) * 100.0)), 1)

    top_20_count = min(n, max(1, int(n * 0.20)))
    top_20_sum = float(sorted_vals.head(top_20_count)[target_col].sum() or 0.0)
    top_20_share = round(min(100.0, max(0.0, (top_20_sum / total_val) * 100.0)), 1)

    is_pareto = top_20_share >= 60.0

    return {
        "applicable": True,
        "column": target_col,
        "is_pareto": is_pareto,
        "top_20_pct_volume_share": top_20_share,
        "pct_records_generating_80_pct": pct_rows_for_80,
        "records_generating_80_pct": rows_for_80,
        "total_records_evaluated": n,
        "total_volume": round(total_val, 2),
        "summary": (
            f"Top 20% of records account for {top_20_share}% of total `{target_col}`. "
            f"80% of total volume is concentrated in {pct_rows_for_80}% of observations "
            f"({rows_for_80:,} of {n:,} records)."
        )
    }


def _missingness_alerts(df: pl.DataFrame) -> list[dict[str, Any]]:
    n = df.height
    alerts = []
    if n == 0:
        return alerts
    for col in df.columns:
        null_cnt = int(df.get_column(col).null_count())
        if null_cnt > 0:
            pct = round((null_cnt / n) * 100.0, 2)
            if pct >= 50.0:
                severity = "critical"
                strategy = "Drop column (exceeds 50% missingness threshold) or investigate systemic data ingestion failure."
            elif pct >= 20.0:
                severity = "high"
                strategy = "Profile missingness mechanism (MCAR vs MAR/MNAR); domain-approved imputation or dedicated missingness indicator required."
            elif pct >= 5.0:
                severity = "medium"
                strategy = "Apply robust central tendency imputation (median/mode) or predictive model-based imputation."
            else:
                severity = "low"
                strategy = "Simple mean/median/mode imputation or listwise record deletion."

            alerts.append({
                "column": col,
                "missing_count": null_cnt,
                "missing_pct": pct,
                "severity": severity,
                "recommended_strategy": strategy,
            })
    alerts.sort(key=lambda x: x["missing_pct"], reverse=True)
    return alerts


def _ml_readiness_warnings(
    df: pl.DataFrame,
    numeric: list[str],
    categorical: list[str],
    correlations: dict[str, dict[str, float | None]],
    numeric_summary: dict[str, Any],
    categorical_summary: dict[str, Any],
) -> dict[str, Any]:
    n = df.height
    multicollinearity_flags = []
    zero_variance_flags = []
    high_cardinality_flags = []

    # 1. Multicollinearity: |r| > 0.85
    seen_pairs = set()
    for col1, row in correlations.items():
        for col2, r_val in row.items():
            if col1 != col2 and r_val is not None and abs(r_val) > 0.85:
                pair_key = tuple(sorted([col1, col2]))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    clamped_r = max(-1.0, min(1.0, r_val))
                    multicollinearity_flags.append({
                        "feature_1": pair_key[0],
                        "feature_2": pair_key[1],
                        "pearson_r": round(clamped_r, 4),
                        "recommendation": f"Severe multicollinearity (|r| = {abs(clamped_r):.2f} > 0.85). Remove one feature or apply PCA/regularization before linear modeling.",
                    })

    # 2. Zero-variance & Constant features
    for col in numeric:
        p = numeric_summary.get(col, {})
        std = p.get("std")
        val_min = p.get("min")
        val_max = p.get("max")
        if (std == 0.0 or (val_min is not None and val_min == val_max)) and p.get("count", 0) > 1:
            zero_variance_flags.append({
                "column": col,
                "type": "numeric",
                "constant_value": val_min,
                "recommendation": "Zero variance detected (all values identical). Drop feature as it provides zero predictive information.",
            })

    for col in categorical:
        p = categorical_summary.get(col, {})
        if p.get("unique", 0) <= 1 and n > 1:
            zero_variance_flags.append({
                "column": col,
                "type": "categorical",
                "constant_value": p.get("top_values", [{}])[0].get("value") if p.get("top_values") else None,
                "recommendation": "Zero categorical diversity (only 1 unique value). Drop before training.",
            })

    # 3. High cardinality text / IDs
    for col in categorical:
        p = categorical_summary.get(col, {})
        unique_cnt = p.get("unique", 0)
        card_ratio = p.get("cardinality_ratio") or 0.0
        if unique_cnt > 50 or card_ratio > 0.5:
            high_cardinality_flags.append({
                "column": col,
                "unique_count": unique_cnt,
                "cardinality_ratio": round(card_ratio, 4),
                "recommendation": "High cardinality feature. One-hot encoding will expand dimensionality uncontrollably; consider frequency encoding, target encoding, or entity embeddings.",
            })

    candidate_targets = []
    for col in numeric:
        col_lower = col.lower()
        if any(term in col_lower for term in ["revenue", "sales", "price", "profit", "target", "churn", "score", "rating"]):
            candidate_targets.append({"column": col, "task": "Regression / Forecasting", "type": "numeric"})
    for col in categorical:
        col_lower = col.lower()
        if categorical_summary.get(col, {}).get("unique", 0) in [2, 3]:
            candidate_targets.append({"column": col, "task": "Classification", "type": "categorical"})

    is_ready = len(zero_variance_flags) == 0 and len(multicollinearity_flags) == 0

    return {
        "status": "ready" if is_ready else "warnings_detected",
        "multicollinearity_flags": multicollinearity_flags,
        "zero_variance_columns": zero_variance_flags,
        "high_cardinality_columns": high_cardinality_flags,
        "candidate_targets": candidate_targets,
    }

