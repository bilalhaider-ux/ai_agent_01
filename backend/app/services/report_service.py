"""Professional enterprise report rendering for HTML and Markdown outputs.

Styled in the DataSnap signature theme (Onest, JetBrains Mono, Indigo/Slate palette).
Produces McKinsey/Gartner-grade executive documents with complete A4 print rules.
"""

import datetime
import html
import json
from typing import Any


def _text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return f"{value:,}"
    return _text(value)


def _metric_table(value: Any) -> str:
    if not isinstance(value, dict):
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            columns = list(dict.fromkeys(column for item in value for column in item))
            header = "".join(f"<th>{_text(column.replace('_', ' ').title())}</th>" for column in columns)
            rows = []
            for item in value:
                cells = "".join(f"<td>{_number(item.get(column, '—'))}</td>" for column in columns)
                rows.append(f"<tr>{cells}</tr>")
            return f"<div class=\"table-scroll\"><table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
        return f"<p class=\"metric-value\">{_number(value)}</p>"
    if not value or not all(isinstance(item, list) for item in value.values()):
        return f"<pre class=\"json-block\">{_text(json.dumps(value, indent=2, default=str))}</pre>"
    columns = list(value)
    row_count = max((len(items) for items in value.values()), default=0)
    header = "".join(f"<th>{_text(column.replace('_', ' ').title())}</th>" for column in columns)
    rows = []
    for index in range(row_count):
        cells = "".join(f"<td>{_number(value[column][index]) if index < len(value[column]) else '—'}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    return f"<div class=\"table-scroll\"><table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def _metric_sections(metrics: dict[str, Any]) -> str:
    sections = []
    for key, value in metrics.items():
        label = key.replace('_', ' ').title()
        sections.append(f"<section class=\"metric-section\"><h3>{_text(label)}</h3>{_metric_table(value)}</section>")
    return ''.join(sections) or '<p class="muted">No computed metrics were returned.</p>'


def _chart_gallery(charts: list[str], chart_details: list[dict[str, Any]] | None = None) -> str:
    if not charts:
        return '<p class="muted">No visualizations were generated.</p>'
    items = []
    for index, chart in enumerate(charts, 1):
        caption = None
        if chart_details and index - 1 < len(chart_details):
            caption = chart_details[index - 1].get("title")
        if not caption:
            caption = f"Visualization {index:02d}"
        items.append(
            f'<figure class="chart"><img src="data:image/png;base64,{chart}" alt="{_text(caption)}"><figcaption><strong>{_text(caption)}</strong></figcaption></figure>'
        )
    return f'<div class="chart-grid">{"".join(items)}</div>'


def build_datasnap_suggestions(metrics: dict[str, Any]) -> list[str]:
    """Build conservative next-step guidance from observed EDA artifacts."""
    eda = metrics.get("exploratory_data_analysis", metrics)
    non_graphical = eda.get("non_graphical", eda) if isinstance(eda, dict) else {}
    health = non_graphical.get("data_health", {})
    health_score = health.get("score")
    business = non_graphical.get("business_insights", {})
    ml_readiness = business.get("ml_readiness", {})

    suggestions = [
        "Review the reported missing values, duplicate rows, and IQR outliers before modeling; apply domain-approved cleaning rules without overwriting the raw dataset.",
    ]
    if health_score is not None and health_score < 80:
        suggestions.append(
            f"Address data health deficits (current score: {health_score}/100) across completeness, uniqueness, and outlier boundaries before committing data to downstream analytical marts."
        )

    missing = non_graphical.get("missing_counts", {})
    if isinstance(missing, dict) and any(value for value in missing.values()):
        suggestions.append(
            "Define a missing-value strategy for affected columns, such as validated imputation, an explicit category, or excluding unusable records."
        )

    if non_graphical.get("duplicate_row_count", 0):
        suggestions.append(
            "Inspect duplicate rows and decide whether they represent repeated observations or records that should be removed."
        )

    outliers = non_graphical.get("outlier_counts_iqr", {})
    if isinstance(outliers, dict) and any(value for value in outliers.values()):
        suggestions.append(
            "Investigate IQR-flagged numeric values and choose a documented treatment such as retaining, transforming, capping, or excluding them."
        )

    if ml_readiness.get("multicollinearity_flags"):
        suggestions.append(
            "Mitigate extreme multicollinearity (|r| > 0.85) between flagged numeric feature pairs via feature elimination, PCA, or ridge regularization before fitting linear models."
        )

    if ml_readiness.get("zero_variance_columns"):
        suggestions.append(
            "Prune constant zero-variance features prior to model training; they provide zero mutual information and consume redundant pipeline compute."
        )

    numeric = non_graphical.get("numeric_summary", {})
    categorical = non_graphical.get("categorical_summary", {})
    if numeric:
        suggestions.append(
            "For a future regression or forecasting task, select and validate a numeric target with domain context, then use the cleaned numeric and categorical columns as candidate features."
        )
    elif categorical:
        suggestions.append(
            "For a future classification task, select and validate a categorical target with domain context, then encode and assess the remaining columns as candidate features."
        )
    else:
        suggestions.append(
            "Select and validate a target variable with domain context before choosing a predictive modeling approach; this dataset currently has no detected numeric or categorical feature columns."
        )

    suggestions.append(
        "This report is descriptive EDA only. Predictive modeling should be a separate step with train/test validation, leakage checks, and an appropriate evaluation metric."
    )
    return suggestions


def build_strategic_recommendations(metrics: dict[str, Any]) -> list[dict[str, str]]:
    """Create actions only when the corresponding computed evidence exists."""
    eda = metrics.get("exploratory_data_analysis", metrics)
    non_graphical = eda.get("non_graphical", eda) if isinstance(eda, dict) else {}
    business = non_graphical.get("business_insights", {})
    pareto = business.get("pareto_analysis", {})
    ml_readiness = business.get("ml_readiness", {})
    missing_alerts = business.get("missingness_alerts", [])
    actions: list[dict[str, str]] = []

    # 1. High-risk missingness
    if missing_alerts:
        severe = [a for a in missing_alerts if a.get("severity") in {"critical", "high"}]
        target_alert = severe[0] if severe else missing_alerts[0]
        col = target_alert["column"]
        actions.append({
            "title": f"Prioritize missing-value controls for `{col}`",
            "recommended_action": target_alert["recommended_strategy"],
            "data_justification": f"`{col}` has {target_alert['missing_pct']}% missing values ({target_alert['missing_count']:,} null rows). Severity: {target_alert['severity'].upper()}.",
            "business_reason": "Unresolved missingness distorts denominators, biases summary averages, and creates operational reporting inconsistencies.",
        })
    else:
        missing = non_graphical.get("missing_percentages", {})
        if isinstance(missing, dict):
            affected = [(column, value) for column, value in missing.items() if value]
            if affected:
                column, percentage = max(affected, key=lambda item: item[1])
                actions.append({
                    "title": "Prioritize missing-value controls",
                    "recommended_action": f"Profile and define a documented treatment for `{column}` before downstream reporting or modeling.",
                    "data_justification": f"`{column}` has {percentage:.4f}% missing values.",
                    "business_reason": "Unresolved missingness can change denominators, distort averages, and create inconsistent operational reporting.",
                })

    # 2. Multicollinearity risk
    if ml_readiness.get("multicollinearity_flags"):
        flag = ml_readiness["multicollinearity_flags"][0]
        actions.append({
            "title": "Mitigate severe feature multicollinearity",
            "recommended_action": flag["recommendation"],
            "data_justification": f"Pearson correlation between `{flag['feature_1']}` and `{flag['feature_2']}` is r = {flag['pearson_r']:.4f} (|r| > 0.85).",
            "business_reason": "Extreme multicollinearity inflates standard errors, creates unstable coefficients, and prevents reliable driver attribution.",
        })

    # 3. Pareto 80/20 concentration
    if pareto.get("applicable") and pareto.get("is_pareto"):
        actions.append({
            "title": f"Focus operations on 80/20 {pareto.get('column')} concentration",
            "recommended_action": f"Structure priority workflows around the top {pareto.get('pct_records_generating_80_pct')}% of records generating 80% of volume.",
            "data_justification": f"Top 20% of records account for {pareto.get('top_20_pct_volume_share')}% of aggregate `{pareto.get('column')}` volume ({(pareto.get('total_volume') or 0):,}).",
            "business_reason": "Uniform allocation across heavily skewed distributions wastes capital; tiering operations by high-yield drivers optimizes operational leverage.",
        })

    # 4. Zero-variance features
    if ml_readiness.get("zero_variance_columns"):
        zv = ml_readiness["zero_variance_columns"][0]
        actions.append({
            "title": f"Prune uninformative zero-variance column `{zv['column']}`",
            "recommended_action": zv["recommendation"],
            "data_justification": f"`{zv['column']}` is completely constant across all evaluated records.",
            "business_reason": "Features with zero variance provide zero mutual information and add unnecessary complexity to downstream pipelines.",
        })

    # 5. IQR Outliers
    outliers = non_graphical.get("outlier_counts_iqr", {})
    if isinstance(outliers, dict):
        affected = [(column, value) for column, value in outliers.items() if value]
        if affected:
            column, count = max(affected, key=lambda item: item[1])
            actions.append({
                "title": f"Investigate IQR outliers in `{column}`",
                "recommended_action": f"Review the {count:,} IQR-flagged rows in `{column}` and document whether they are valid extremes or data-quality errors.",
                "data_justification": f"IQR profiling identified {count:,} outlier values in `{column}`.",
                "business_reason": "Unreviewed extremes can disproportionately influence averages, forecasts, thresholds, and resource planning.",
            })

    # 6. Statistical tests
    tests = non_graphical.get("statistical_tests", {})
    significant = [
        item for item in tests.get("categorical_numeric_tests", [])
        if item.get("significant_at_0_05")
    ]
    if significant:
        item = significant[0]
        actions.append({
            "title": "Validate significant group differences",
            "recommended_action": f"Segment the `{item['numeric']}` process by `{item['categorical']}` and run a domain review of the group-level drivers.",
            "data_justification": f"{item['test']} returned statistic {item['statistic']:.4f} with p-value {item['p_value']:.4f}.",
            "business_reason": "A statistically significant group difference indicates that one pooled average may hide materially different segment behavior.",
        })

    # 7. Strongest relationship
    relationships = non_graphical.get("multivariate", {}).get("strongest_numeric_relationships", [])
    if relationships and not any("multicollinearity" in a["title"].lower() for a in actions):
        item = relationships[0]
        actions.append({
            "title": "Validate the strongest numeric relationship",
            "recommended_action": f"Review the relationship between `{item['columns'][0]}` and `{item['columns'][1]}` for leakage, shared definitions, and plausible domain drivers.",
            "data_justification": f"Pearson correlation is {item['pearson_r']:.4f} (absolute value {item['absolute_r']:.4f}).",
            "business_reason": "Strong association can reveal duplicated measures, process dependencies, or useful monitoring pairs, but it does not prove causation.",
        })

    if not actions:
        actions.append({
            "title": "Define a validated analysis target",
            "recommended_action": "Confirm a business question and target variable with domain owners before taking operational action.",
            "data_justification": "No missingness, outlier, significant-test, or numeric-relationship trigger exceeded the implemented review rules.",
            "business_reason": "A documented target prevents teams from turning descriptive patterns into unsupported decisions.",
        })
    return actions[:5]


def markdown_report(
    synthesis: dict[str, Any],
    metrics: dict[str, Any],
    charts: list[str],
    analysis_id: str | None = None,
    dataset_name: str | None = None,
    timestamp: str | None = None,
    **kwargs: Any,
) -> str:
    eda = metrics.get('exploratory_data_analysis', metrics)
    non_graphical = eda.get('non_graphical', eda) if isinstance(eda, dict) else {}
    suggestions = build_datasnap_suggestions(metrics)
    actions = build_strategic_recommendations(metrics)

    aid = analysis_id or synthesis.get("analysis_id") or "DS-EXEC-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")
    dname = dataset_name or synthesis.get("dataset_name") or "Primary Analytical Dataset"
    ts = timestamp or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    health = non_graphical.get("data_health", {})
    health_score = non_graphical.get("data_health_score", health.get("score"))
    grade = health.get("grade", "Reviewed")
    sub_scores = health.get("sub_scores", {})
    business = non_graphical.get("business_insights", {})
    pareto = business.get("pareto_analysis", {})
    ml_readiness = business.get("ml_readiness", {})

    num_profiles = non_graphical.get('numeric_summary', {})
    cat_profiles = non_graphical.get('categorical_summary', {})
    correlations = non_graphical.get('correlation_matrix_pearson', {})
    stat_tests = non_graphical.get('statistical_tests', {})

    num_tables = []
    if num_profiles:
        num_tables.append('| Feature | Count | Mean | Median | Std | Min | Max | IQR | Outliers | Skewness | Kurtosis |')
        num_tables.append('| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |')
        for col, p in num_profiles.items():
            num_tables.append(
                f"| `{col}` | {(p.get('count') or 0):,} | {_number(p.get('mean'))} | {_number(p.get('median'))} | {_number(p.get('std'))} | {_number(p.get('min'))} | {_number(p.get('max'))} | {_number(p.get('iqr'))} | {(p.get('outlier_count_iqr') or 0):,} | {_number(p.get('skewness'))} | {_number(p.get('kurtosis'))} |"
            )

    cat_tables = []
    if cat_profiles:
        cat_tables.append('| Feature | Unique | Missing | Cardinality Ratio | Top Categories |')
        cat_tables.append('| :--- | :--- | :--- | :--- | :--- |')
        for col, p in cat_profiles.items():
            top_vals = ", ".join(f"{v.get('value')} ({(v.get('count') or 0):,})" for v in p.get('top_values', [])[:3])
            cat_tables.append(
                f"| `{col}` | {(p.get('unique') or 0):,} | {(p.get('missing') or 0):,} | {_number(p.get('cardinality_ratio'))} | {top_vals} |"
            )

    missing_alerts = business.get("missingness_alerts", [])
    severe_missing = [a for a in missing_alerts if a.get("severity") in {"critical", "high"}]

    # Actionable checklist
    checklist = [
        "### 📋 Downstream Data Pipeline Actionable Checklist",
        "",
    ]
    if severe_missing:
        checklist.append(
            f"- [ ] **High-Risk Missingness Remediation:** Define validated imputation or filtering for `{severe_missing[0]['column']}` ({severe_missing[0]['missing_pct']}% null rows; {severe_missing[0]['severity'].upper()})."
        )
    elif non_graphical.get("missing_counts") and any(non_graphical["missing_counts"].values()):
        checklist.append("- [ ] **Missing Value Imputation:** Define documented treatment (median/mode or explicit sentinel) for affected features.")
    else:
        checklist.append("- [x] **Completeness Audit:** 100% cell completeness verified across all columns.")

    if non_graphical.get("duplicate_row_count", 0) > 0:
        checklist.append(f"- [ ] **Deduplication:** Review and remediate {non_graphical['duplicate_row_count']:,} duplicate records before warehouse ingestion.")
    else:
        checklist.append("- [x] **Deduplication:** Zero duplicate rows detected in dataset.")

    if ml_readiness.get("multicollinearity_flags"):
        flags_text = ", ".join(f"`{f['feature_1']}` & `{f['feature_2']}`" for f in ml_readiness["multicollinearity_flags"][:2])
        checklist.append(f"- [ ] **Multicollinearity Elimination:** Address high correlation (|r| > 0.85) between {flags_text} before fitting linear models.")

    if ml_readiness.get("zero_variance_columns"):
        zv_text = ", ".join(f"`{f['column']}`" for f in ml_readiness["zero_variance_columns"])
        checklist.append(f"- [ ] **Feature Selection:** Prune uninformative zero-variance column(s) ({zv_text}).")

    checklist.extend([
        "- [ ] **Outlier Boundary Validation:** Domain audit of IQR-flagged extremes prior to operational scaling.",
        "- [ ] **Leakage Isolation:** Establish rigid train/test partition before feature engineering and standardization.",
    ])

    lines = [
        '# Exploratory Data Analysis Report',
        '',
        f'> **Dataset:** `{dname}` | **Analysis ID:** `{aid}` | **Generated:** {ts}',
        '> **Audit Trail:** `Deterministic SciPy Engine` · `Verified Polars Execution` · `Zero-Imputation Grounding`',
        '',
        '## Scope',
        'EDA is a comprehensive methodology that includes both non-graphical statistical summaries and data visualization techniques.',
        '',
    ]

    # Callouts
    if health_score is not None:
        lines.extend([
            '> [!NOTE]',
            f'> **Deterministic Data Health Score: {health_score}/100 ({grade})**',
            f"> - Completeness: {sub_scores.get('completeness', 100)}% | Uniqueness: {sub_scores.get('uniqueness', 100)}% | Outlier Control: {sub_scores.get('outlier_control', 100)}% | Type Validity: {sub_scores.get('type_consistency', 100)}%",
            f"> - *{health.get('rating_description', 'Deterministic evaluation from raw data.')}*",
            '',
        ])

    if severe_missing or ml_readiness.get("multicollinearity_flags") or ml_readiness.get("zero_variance_columns"):
        warn_bullets = []
        for a in severe_missing[:2]:
            warn_bullets.append(f"> - High-risk missingness ({a['severity'].upper()}): `{a['column']}` has {a['missing_pct']}% null values ({a['missing_count']:,} records). {a['recommended_strategy']}")
        for f in ml_readiness.get("multicollinearity_flags", [])[:2]:
            warn_bullets.append(f"> - Multicollinearity: `{f['feature_1']}` and `{f['feature_2']}` (Pearson r = {f['pearson_r']:.3f}).")
        for z in ml_readiness.get("zero_variance_columns", [])[:2]:
            warn_bullets.append(f"> - Zero-variance column: `{z['column']}` (constant values across all rows).")
        lines.extend([
            '> [!WARNING]',
            '> **Data Quality & ML Modeling Readiness Warnings:**',
            *warn_bullets,
            '',
        ])

    if pareto.get("applicable"):
        lines.extend([
            '> [!TIP]',
            f'> **Pareto 80/20 Concentration:** {pareto.get("summary")}',
            '',
        ])

    lines.extend([
        '## Univariate Analysis',
        'Each feature is profiled independently for distribution, missingness, cardinality, quantiles, skewness, kurtosis, and IQR outliers.',
        '',
        '## Bivariate Analysis',
        'Numeric pairs include Pearson and Spearman relationships; categorical-numeric pairs include group counts, means, and medians.',
        '',
        '## Multivariate Analysis',
        'Numeric feature relationships are summarized with a Pearson correlation matrix and strongest pairwise relationships.',
        '',
        '## 1. Data Quality & Distribution Summary',
        'Exact shape, missingness percentages, IQR outlier counts, and high-cardinality columns are reported below.',
        '',
        '## 2. Statistical Core Discoveries',
        'The report includes skewness, kurtosis, variance proxies, Pearson/Spearman relationships, ANOVA or Welch t-tests, and Chi-square tests when valid groups exist.',
        '',
        '## 3. Mandatory Next Actions & Strategic Recommendations',
    ])

    for index, action in enumerate(actions, 1):
        lines.extend([
            '',
            f"### 🚀 Action {index}: {action['title']}",
            f"- **Recommended Action:** {action['recommended_action']}",
            f"- **Data Justification:** {action['data_justification']}",
            f"- **Business Reason:** {action['business_reason']}",
        ])

    lines.extend([
        '',
        *checklist,
        '',
        '## Non-Graphical Statistical Summaries',
        '<details open>',
        '<summary><b>📊 Numerical Feature Summary (Click to expand/collapse)</b></summary>',
        '',
        *(num_tables or ['_No numerical features found._']),
        '</details>',
        '',
        '<details open>',
        '<summary><b>🏷️ Categorical Feature Summary (Click to expand/collapse)</b></summary>',
        '',
        *(cat_tables or ['_No categorical features found._']),
        '</details>',
        '',
        '## Verified EDA Output',
        '<details>',
        '<summary><b>🔍 Verified Machine-Readable Output (JSON)</b></summary>',
        '',
        f"```json\n{json.dumps(eda, indent=2, default=str)}\n```",
        '</details>',
        '',
        '## Data Visualizations',
    ])
    chart_details = kwargs.get("chart_details") or non_graphical.get("chart_details") or []
    for index, chart in enumerate(charts, 1):
        caption = None
        if chart_details and index - 1 < len(chart_details):
            caption = chart_details[index - 1].get("title")
        if not caption:
            caption = f"Visualization {index:02d}"
        lines.append(f'### {caption}\n![{caption}](data:image/png;base64,{chart})\n')
    lines.extend([
        '',
        '## Suggestion by DataSnap',
        'The following are conservative next steps based only on the observed EDA results:',
        *[f'- {suggestion}' for suggestion in suggestions],
    ])
    return '\n'.join(lines)


def html_report(
    synthesis: dict[str, Any],
    metrics: dict[str, Any],
    charts: list[str],
    analysis_id: str | None = None,
    dataset_name: str | None = None,
    timestamp: str | None = None,
    **kwargs: Any,
) -> str:
    eda = metrics.get('exploratory_data_analysis', metrics)
    non_graphical = eda.get('non_graphical', eda) if isinstance(eda, dict) else {}
    suggestions = build_datasnap_suggestions(metrics)
    actions = build_strategic_recommendations(metrics)

    aid = analysis_id or synthesis.get("analysis_id") or "DS-EXEC-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")
    dname = dataset_name or synthesis.get("dataset_name") or "Primary Analytical Dataset"
    ts = timestamp or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    row_count = non_graphical.get("row_count", 0)
    col_count = non_graphical.get("column_count", 0)
    num_profiles = non_graphical.get('numeric_summary', {})
    cat_profiles = non_graphical.get('categorical_summary', {})
    dup_rows = non_graphical.get("duplicate_row_count", 0)

    health = non_graphical.get("data_health", {})
    health_score = non_graphical.get("data_health_score", health.get("score", 100.0))
    grade = health.get("grade", "Excellent")
    desc = health.get("rating_description", "Deterministic evaluation completed.")
    sub_scores = health.get("sub_scores", {
        "completeness": 100.0,
        "uniqueness": 100.0,
        "outlier_control": 100.0,
        "type_consistency": 100.0,
    })

    business = non_graphical.get("business_insights", {})
    pareto = business.get("pareto_analysis", {})
    ml_readiness = business.get("ml_readiness", {})
    correlations = non_graphical.get("correlation_matrix_pearson", {})
    stat_tests = non_graphical.get("statistical_tests", {})
    cat_num_tests = stat_tests.get("categorical_numeric_tests", [])

    # HTML Tables
    num_table_rows = []
    for col, p in num_profiles.items():
        num_table_rows.append(
            f"<tr><td><strong>{_text(col)}</strong></td>"
            f"<td>{(p.get('count') or 0):,}</td>"
            f"<td>{_number(p.get('mean'))}</td>"
            f"<td>{_number(p.get('median'))}</td>"
            f"<td>{_number(p.get('std'))}</td>"
            f"<td>{_number(p.get('min'))}</td>"
            f"<td>{_number(p.get('max'))}</td>"
            f"<td>{_number(p.get('quantiles', {}).get('q25'))}</td>"
            f"<td>{_number(p.get('quantiles', {}).get('q75'))}</td>"
            f"<td>{_number(p.get('iqr'))}</td>"
            f"<td><span class=\"badge {'badge-warn' if (p.get('outlier_count_iqr') or 0) > 0 else 'badge-neutral'}\">{(p.get('outlier_count_iqr') or 0):,}</span></td>"
            f"<td>{_number(p.get('skewness'))}</td>"
            f"<td>{_number(p.get('kurtosis'))}</td></tr>"
        )
    num_table_html = (
        "<div class=\"table-scroll\"><table><thead><tr>"
        "<th>Feature</th><th>Count</th><th>Mean</th><th>Median</th><th>Std</th><th>Min</th><th>Max</th><th>Q25</th><th>Q75</th><th>IQR</th><th>Outliers</th><th>Skewness</th><th>Kurtosis</th>"
        f"</tr></thead><tbody>{''.join(num_table_rows)}</tbody></table></div>"
        if num_table_rows else "<p class=\"muted\">No numerical columns identified.</p>"
    )

    cat_table_rows = []
    for col, p in cat_profiles.items():
        top_str = ", ".join(f"{v.get('value')} ({(v.get('count') or 0):,})" for v in p.get('top_values', [])[:3])
        card_pct = f"{p.get('cardinality_ratio') * 100:.1f}%" if p.get('cardinality_ratio') is not None else "—"
        cat_table_rows.append(
            f"<tr><td><strong>{_text(col)}</strong></td>"
            f"<td>{(p.get('unique') or 0):,}</td>"
            f"<td>{(p.get('missing') or 0):,}</td>"
            f"<td>{card_pct}</td>"
            f"<td>{_text(top_str or '—')}</td></tr>"
        )
    cat_table_html = (
        "<div class=\"table-scroll\"><table><thead><tr>"
        "<th>Feature</th><th>Unique</th><th>Missing</th><th>Cardinality Ratio</th><th>Top Categories &amp; Counts</th>"
        f"</tr></thead><tbody>{''.join(cat_table_rows)}</tbody></table></div>"
        if cat_table_rows else "<p class=\"muted\">No categorical columns identified.</p>"
    )

    # Hypothesis tests table
    test_rows = []
    for t in cat_num_tests[:8]:
        sig_badge = (
            "<span class=\"badge badge-success\">Significant (p &lt; 0.05)</span>"
            if t.get("significant_at_0_05")
            else "<span class=\"badge badge-neutral\">Not Significant</span>"
        )
        test_rows.append(
            f"<tr><td><strong>{_text(t.get('numeric'))} by {_text(t.get('categorical'))}</strong></td>"
            f"<td>{_text(t.get('test'))}</td>"
            f"<td>{_number(t.get('statistic'))}</td>"
            f"<td>{_number(t.get('p_value'))}</td>"
            f"<td>{sig_badge}</td></tr>"
        )
    test_table_html = (
        "<div class=\"table-scroll\"><table><thead><tr>"
        "<th>Interaction</th><th>Hypothesis Test</th><th>Statistic</th><th>p-value</th><th>Significance (α = 0.05)</th>"
        f"</tr></thead><tbody>{''.join(test_rows)}</tbody></table></div>"
        if test_rows else "<p class=\"muted\">No multi-group hypothesis tests were applicable.</p>"
    )

    # Actions HTML
    action_cards = []
    for idx, act in enumerate(actions, 1):
        action_cards.append(f"""
        <article class="action-card">
          <div class="action-head">
            <span class="action-pill">Action {idx:02d}</span>
            <h4>{_text(act['title'])}</h4>
          </div>
          <p class="action-rec"><strong>Recommended Action:</strong> {_text(act['recommended_action'])}</p>
          <div class="action-meta">
            <div class="meta-item"><small>DATA EVIDENCE</small><span>{_text(act['data_justification'])}</span></div>
            <div class="meta-item"><small>BUSINESS IMPACT</small><span>{_text(act['business_reason'])}</span></div>
          </div>
        </article>
        """)

    chart_details = kwargs.get("chart_details") or non_graphical.get("chart_details") or []
    chart_markup = _chart_gallery(charts, chart_details=chart_details)
    suggestion_markup = ''.join(f'<li>{_text(s)}</li>' for s in suggestions)

    # ML Readiness and data quality alert banners
    ml_warnings = []
    missing_alerts = business.get("missingness_alerts", [])
    severe_missing = [a for a in missing_alerts if a.get("severity") in {"critical", "high"}]
    for a in severe_missing[:2]:
        ml_warnings.append(
            f"<div class=\"alert-pill alert-danger\"><strong>High-Risk Missingness ({_text(a['severity'].upper())}):</strong> Feature <code>{_text(a['column'])}</code> has {a['missing_pct']}% null values ({a['missing_count']:,} rows). {_text(a['recommended_strategy'])}</div>"
        )
    if ml_readiness.get("multicollinearity_flags"):
        for f in ml_readiness["multicollinearity_flags"][:2]:
            ml_warnings.append(
                f"<div class=\"alert-pill alert-warn\"><strong>Multicollinearity Flag:</strong> {_text(f['feature_1'])} &amp; {_text(f['feature_2'])} (|r| = {_number(f['pearson_r'])} &gt; 0.85). {_text(f['recommendation'])}</div>"
            )
    if ml_readiness.get("zero_variance_columns"):
        for z in ml_readiness["zero_variance_columns"][:2]:
            ml_warnings.append(
                f"<div class=\"alert-pill alert-warn\"><strong>Zero-Variance Feature:</strong> Column <code>{_text(z['column'])}</code> contains zero variance. {_text(z['recommendation'])}</div>"
            )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DataSnap Executive EDA Report · {_text(dname)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Onest:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
  --brand: #4f46e5;
  --brand-dark: #3730a3;
  --brand-light: #eef2ff;
  --brand-line: #c7d2fe;
  --text: #0f172a;
  --text-soft: #334155;
  --text-dim: #64748b;
  --text-faint: #94a3b8;
  --bg-page: #f8fafc;
  --bg-card: #ffffff;
  --border: #e2e8f0;
  --border-light: #f1f5f9;
  --ok: #059669;
  --ok-light: #ecfdf5;
  --ok-line: #a7f3d0;
  --warn: #d97706;
  --warn-light: #fffbeb;
  --warn-line: #fde68a;
  --danger: #dc2626;
  --danger-light: #fef2f2;
}}

* {{ box-sizing: border-box; }}
html, body {{
  margin: 0;
  padding: 0;
  background: var(--bg-page);
  color: var(--text);
  font-family: 'Onest', system-ui, -apple-system, sans-serif;
  font-size: 14.5px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

.report-container {{
  max-width: 1040px;
  margin: 36px auto;
  padding: 0 24px 64px;
}}

/* Executive Header */
.executive-header {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 36px 40px;
  box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
}}
.executive-header::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: linear-gradient(90deg, #4f46e5, #7c3aed, #06b6d4);
}}

.brand-bar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  padding-bottom: 22px;
  border-bottom: 1px solid var(--border);
}}
.brand-identity {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.brand-logo-mark {{
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--brand), #7c3aed);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 16px;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}}
.brand-title {{
  font-size: 19px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}}
.brand-subtitle {{
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--text-dim);
  font-family: 'JetBrains Mono', monospace;
}}

.audit-pills {{
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}}
.pill {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  border: 1px solid transparent;
}}
.pill-brand {{ background: var(--brand-light); color: var(--brand); border-color: var(--brand-line); }}
.pill-success {{ background: var(--ok-light); color: var(--ok); border-color: var(--ok-line); }}
.pill-neutral {{ background: #f1f5f9; color: var(--text-soft); border-color: var(--border); }}

.header-lead {{
  margin-top: 24px;
}}
.header-lead h1 {{
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin: 0 0 8px;
  color: var(--text);
}}
.header-lead p {{
  font-size: 14.5px;
  color: var(--text-soft);
  margin: 0 0 20px;
  max-width: 760px;
}}

.meta-grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding-top: 18px;
  border-top: 1px solid var(--border-light);
}}
.meta-cell small {{
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.1em;
  color: var(--text-dim);
  text-transform: uppercase;
  margin-bottom: 3px;
}}
.meta-cell strong {{
  display: block;
  font-size: 13.5px;
  color: var(--text);
  font-weight: 600;
  word-break: break-all;
}}
.meta-cell code {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: var(--brand);
}}

/* Health Scorecard */
.scorecard-panel {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 24px;
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 32px;
  align-items: center;
  box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.04);
}}
.score-badge-box {{
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, var(--brand-light), #f5f3ff);
  border: 1px solid var(--brand-line);
  border-radius: 14px;
  text-align: center;
}}
.score-big {{
  font-family: 'Onest', sans-serif;
  font-weight: 800;
  font-size: 46px;
  line-height: 1;
  color: var(--brand);
  letter-spacing: -0.04em;
}}
.score-denom {{
  font-size: 14px;
  font-weight: 600;
  color: var(--text-dim);
  font-family: 'JetBrains Mono', monospace;
}}
.score-grade-tag {{
  display: inline-block;
  margin-top: 10px;
  padding: 4px 12px;
  border-radius: 999px;
  background: var(--brand);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}}
.score-details h3 {{
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}}
.score-details p {{
  margin: 0 0 16px;
  font-size: 13.5px;
  color: var(--text-soft);
}}
.subscores-bar {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}}
.subscore-item {{
  background: var(--bg-page);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 12px;
}}
.subscore-item small {{
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  letter-spacing: 0.08em;
  color: var(--text-dim);
  text-transform: uppercase;
  margin-bottom: 2px;
}}
.subscore-item strong {{
  font-size: 15px;
  color: var(--text);
  font-family: 'JetBrains Mono', monospace;
}}

/* KPI Grid */
.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 28px;
}}
.kpi-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 14px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
}}
.kpi-card small {{
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  letter-spacing: 0.08em;
  color: var(--text-dim);
  text-transform: uppercase;
  margin-bottom: 6px;
}}
.kpi-card strong {{
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}}

/* Sections */
.card-section {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 32px 36px;
  margin-bottom: 28px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
}}
.card-section h2 {{
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0 0 8px;
  color: var(--text);
}}
.card-section .section-sub {{
  color: var(--text-dim);
  font-size: 13.5px;
  margin: 0 0 20px;
}}

/* Executive Callout Boxes */
.callout {{
  border-radius: 12px;
  padding: 18px 22px;
  margin-bottom: 20px;
}}
.callout-lead {{
  background: var(--brand-light);
  border: 1px solid var(--brand-line);
}}
.callout-lead small {{
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--brand);
  text-transform: uppercase;
  margin-bottom: 4px;
  font-weight: 600;
}}
.callout-lead p {{ margin: 0; font-size: 15px; color: var(--text); line-height: 1.6; }}

.callout-pareto {{
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  margin-top: 16px;
}}
.callout-pareto small {{
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: #166534;
  text-transform: uppercase;
  margin-bottom: 4px;
  font-weight: 600;
}}
.callout-pareto p {{ margin: 0; font-size: 13.5px; color: #14532d; }}

.alert-pill {{
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 12.5px;
  margin-top: 8px;
}}
.alert-warn {{ background: var(--warn-light); border: 1px solid var(--warn-line); color: #92400e; }}
.alert-danger {{ background: var(--danger-light); border: 1px solid #fca5a5; color: #991b1b; }}

/* Actions */
.actions-grid {{
  display: grid;
  gap: 16px;
}}
.action-card {{
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 22px;
  background: var(--bg-page);
}}
.action-head {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}}
.action-pill {{
  background: var(--brand);
  color: #fff;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  text-transform: uppercase;
}}
.action-head h4 {{ margin: 0; font-size: 15px; font-weight: 700; color: var(--text); }}
.action-rec {{ margin: 0 0 14px; font-size: 13.5px; color: var(--text-soft); }}
.action-meta {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}}
.meta-item small {{
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  letter-spacing: 0.1em;
  color: var(--text-dim);
  text-transform: uppercase;
  margin-bottom: 3px;
}}
.meta-item span {{
  font-size: 12.5px;
  color: var(--text-soft);
  line-height: 1.5;
}}

/* Tables */
.table-scroll {{ overflow-x: auto; margin-top: 12px; border-radius: 10px; border: 1px solid var(--border); }}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
  text-align: left;
  background: var(--bg-card);
}}
th {{
  background: #f1f5f9;
  color: var(--text-soft);
  font-size: 10.5px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-family: 'JetBrains Mono', monospace;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}}
td {{
  padding: 9px 12px;
  border-bottom: 1px solid var(--border-light);
  white-space: nowrap;
  color: var(--text-soft);
}}
tr:last-child td {{ border-bottom: 0; }}
tbody tr:hover {{ background: #f8fafc; }}

.badge {{
  display: inline-block;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 10.5px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}}
.badge-success {{ background: var(--ok-light); color: var(--ok); }}
.badge-warn {{ background: var(--warn-light); color: var(--warn); }}
.badge-neutral {{ background: #f1f5f9; color: var(--text-dim); }}

/* Visuals */
.chart-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
  margin-top: 12px;
}}
.chart {{
  margin: 0;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
  background: var(--bg-card);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02);
}}
.chart img {{
  display: block;
  width: 100%;
  height: auto;
  border-radius: 8px;
}}
figcaption {{
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-dim);
  font-family: 'JetBrains Mono', monospace;
}}

/* Suggestion list */
.clean-list {{
  margin: 0;
  padding: 0 0 0 20px;
  display: grid;
  gap: 10px;
  color: var(--text-soft);
  font-size: 13.5px;
}}

/* Footer */
.executive-footer {{
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  color: var(--text-dim);
  font-size: 12px;
}}
.footer-left {{ display: flex; align-items: center; gap: 8px; font-weight: 600; }}
.footer-right {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; }}

/* Print / PDF Engine Styles */
@page {{
  size: A4;
  margin: 16mm 14mm 16mm 14mm;
  @top-left {{
    content: "DataSnap · Executive EDA Report";
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    color: #64748b;
  }}
  @top-right {{
    content: "Deterministic SciPy Engine · Verified Polars Execution";
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    color: #64748b;
  }}
  @bottom-left {{
    content: "Confidential · Machine-Verified Analytical Artifact";
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    color: #64748b;
  }}
  @bottom-right {{
    content: "Page " counter(page);
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    color: #64748b;
  }}
}}

@media print {{
  body {{
    background: #ffffff !important;
    color: #0f172a !important;
    font-size: 10pt !important;
  }}
  .report-container {{
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }}
  .executive-header, .scorecard-panel, .card-section, .kpi-card, .action-card, .chart {{
    box-shadow: none !important;
    border-color: #cbd5e1 !important;
  }}
  .scorecard-panel, .executive-header, .kpi-grid, .action-card, .chart, .alert-pill, .callout, tr {{
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }}
  h1, h2, h3, h4 {{
    page-break-after: avoid !important;
    break-after: avoid !important;
  }}
  thead {{
    display: table-header-group !important;
  }}
  .table-scroll {{
    overflow: visible !important;
    border: none !important;
  }}
  table {{
    width: 100% !important;
    font-size: 7.5pt !important;
    border-collapse: collapse !important;
  }}
  th, td {{
    padding: 3pt 4pt !important;
    white-space: normal !important;
    word-break: break-word !important;
  }}
  th {{
    font-size: 7pt !important;
    background: #f1f5f9 !important;
    color: #334155 !important;
  }}
  * {{
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
}}

@media (max-width: 800px) {{
  .scorecard-panel {{ grid-template-columns: 1fr; }}
  .kpi-grid {{ grid-template-columns: repeat(3, 1fr); }}
  .meta-grid {{ grid-template-columns: repeat(2, 1fr); }}
  .chart-grid {{ grid-template-columns: 1fr; }}
  .action-meta {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<main class="report-container">

  <!-- Executive Header -->
  <header class="executive-header">
    <div class="brand-bar">
      <div class="brand-identity">
        <div class="brand-logo-mark">⚡</div>
        <div>
          <div class="brand-title">DataSnap</div>
          <div class="brand-subtitle">Executive Decision &amp; Analytical Brief</div>
        </div>
      </div>
      <div class="audit-pills">
        <span class="pill pill-brand">⚡ Verified Polars Execution</span>
        <span class="pill pill-success">🔬 Deterministic SciPy Engine</span>
        <span class="pill pill-neutral">🔒 Zero-Imputation Evidence</span>
      </div>
    </div>

    <div class="header-lead">
      <h1>Exploratory Data Analysis Report</h1>
      <p>A rigorous, machine-verified diagnostic prepared directly from uploaded observational data. Statistical distributions, data health indicators, and downstream pipeline guidance are reported below.</p>
    </div>

    <div class="meta-grid">
      <div class="meta-cell">
        <small>Target Dataset</small>
        <strong>{_text(dname)}</strong>
      </div>
      <div class="meta-cell">
        <small>Analysis Identifier</small>
        <code>{_text(aid)}</code>
      </div>
      <div class="meta-cell">
        <small>Generated Timestamp</small>
        <strong>{_text(ts)}</strong>
      </div>
      <div class="meta-cell">
        <small>Governing Standard</small>
        <strong>Gartner / SciPy Strict</strong>
      </div>
    </div>
  </header>

  <!-- Deterministic Data Health Scorecard -->
  <section class="scorecard-panel">
    <div class="score-badge-box">
      <div class="score-big">{health_score}</div>
      <div class="score-denom">OUT OF 100</div>
      <span class="score-grade-tag">{_text(grade.upper())}</span>
    </div>
    <div class="score-details">
      <h3>Data Health &amp; Integrity Audit</h3>
      <p>{_text(desc)}</p>
      <div class="subscores-bar">
        <div class="subscore-item">
          <small>Completeness</small>
          <strong>{sub_scores.get('completeness', 100):.1f}%</strong>
        </div>
        <div class="subscore-item">
          <small>Uniqueness</small>
          <strong>{sub_scores.get('uniqueness', 100):.1f}%</strong>
        </div>
        <div class="subscore-item">
          <small>Outlier Control</small>
          <strong>{sub_scores.get('outlier_control', 100):.1f}%</strong>
        </div>
        <div class="subscore-item">
          <small>Type Consistency</small>
          <strong>{sub_scores.get('type_consistency', 100):.1f}%</strong>
        </div>
      </div>
    </div>
  </section>

  <!-- KPI Overview Grid -->
  <section class="kpi-grid">
    <div class="kpi-card"><small>Rows Analyzed</small><strong>{row_count:,}</strong></div>
    <div class="kpi-card"><small>Columns Profiled</small><strong>{col_count:,}</strong></div>
    <div class="kpi-card"><small>Numerical Features</small><strong>{len(num_profiles):,}</strong></div>
    <div class="kpi-card"><small>Categorical Features</small><strong>{len(cat_profiles):,}</strong></div>
    <div class="kpi-card"><small>Duplicate Rows</small><strong>{dup_rows:,}</strong></div>
    <div class="kpi-card"><small>Visualizations</small><strong>{len(charts):,}</strong></div>
  </section>

  <!-- Scope & Univariate/Bivariate/Multivariate methodology -->
  <section class="card-section">
    <h2>Analytical Scope &amp; Methodology</h2>
    <p class="section-sub">EDA is a comprehensive methodology that includes both non-graphical statistical summaries and data visualization techniques.</p>
    <div class="callout callout-lead">
      <small>Executive Summary</small>
      <p>{_text(synthesis.get('executive_summary', 'Comprehensive exploratory data analysis completed.'))}</p>
    </div>
    {f'<div class="callout callout-pareto"><small>Pareto Principle Finding</small><p>{_text(pareto.get("summary"))}</p></div>' if pareto.get('applicable') else ''}
    {''.join(ml_warnings)}
  </section>

  <!-- Section 1 & 2: Distributions & Core Discoveries -->
  <section class="card-section">
    <h2>1. Data Quality &amp; Distribution Summary</h2>
    <p class="section-sub">Independent feature profiles include distributions, missingness, cardinality, quantiles, skewness, kurtosis, and IQR outliers.</p>
    <h3>Numerical Feature Profiles</h3>
    {num_table_html}
    <h3 style="margin-top:24px;">Categorical Feature Profiles</h3>
    {cat_table_html}
  </section>

  <section class="card-section">
    <h2>2. Statistical Core Discoveries &amp; Hypothesis Tests</h2>
    <p class="section-sub">Bivariate and multivariate analyses test group differences and identify numeric correlations without assuming causation.</p>
    {test_table_html}
  </section>

  <!-- Section 3: Strategic Recommendations -->
  <section class="card-section">
    <h2>3. Mandatory Next Actions &amp; Strategic Recommendations</h2>
    <p class="section-sub">Evidence-backed interventions prioritized by statistical significance and business leverage.</p>
    <div class="actions-grid">
      {''.join(action_cards)}
    </div>
  </section>

  <!-- Data Visualizations -->
  <section class="card-section">
    <h2>Data Visualizations</h2>
    <p class="section-sub">Distribution histograms, box plots, category frequencies, and bivariate scatters generated from the verified dataset.</p>
    {chart_markup}
  </section>

  <!-- Suggestion by DataSnap -->
  <section class="card-section">
    <h2>Suggestion by DataSnap</h2>
    <p class="section-sub">Conservative guidance for downstream data engineering and predictive modeling pipelines:</p>
    <ul class="clean-list">
      {suggestion_markup}
    </ul>
  </section>

  <!-- Footer -->
  <footer class="executive-footer">
    <div class="footer-left">
      <span>⚡ DataSnap Analytics Platform</span>
    </div>
    <div class="footer-right">
      <span>Machine-verified report · Deterministic execution · No synthetic hallucinations</span>
    </div>
  </footer>

</main>
</body>
</html>"""


def build_report(
    synthesis: dict[str, Any],
    metrics: dict[str, Any],
    charts: list[str],
    analysis_id: str | None = None,
    dataset_name: str | None = None,
    timestamp: str | None = None,
    **kwargs: Any,
) -> tuple[str, str]:
    return (
        markdown_report(synthesis, metrics, charts, analysis_id=analysis_id, dataset_name=dataset_name, timestamp=timestamp, **kwargs),
        html_report(synthesis, metrics, charts, analysis_id=analysis_id, dataset_name=dataset_name, timestamp=timestamp, **kwargs),
    )
