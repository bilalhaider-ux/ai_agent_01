"""Professional report rendering for HTML and Markdown outputs."""

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


def _chart_gallery(charts: list[str]) -> str:
    if not charts:
        return '<p class="muted">No visualizations were generated.</p>'
    items = ''.join(
        f'<figure class="chart"><img src="data:image/png;base64,{chart}" alt="Visualization {index}"><figcaption>Visualization {index}</figcaption></figure>'
        for index, chart in enumerate(charts, 1)
    )
    return f'<div class="chart-grid">{items}</div>'


def build_datasnap_suggestions(metrics: dict[str, Any]) -> list[str]:
    """Build conservative next-step guidance from observed EDA artifacts."""
    eda = metrics.get("exploratory_data_analysis", metrics)
    non_graphical = eda.get("non_graphical", eda) if isinstance(eda, dict) else {}
    suggestions = [
        "Review the reported missing values, duplicate rows, and IQR outliers before modeling; apply domain-approved cleaning rules without overwriting the raw dataset.",
    ]
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
    actions: list[dict[str, str]] = []
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
    outliers = non_graphical.get("outlier_counts_iqr", {})
    if isinstance(outliers, dict):
        affected = [(column, value) for column, value in outliers.items() if value]
        if affected:
            column, count = max(affected, key=lambda item: item[1])
            actions.append({
                "title": "Investigate IQR outliers",
                "recommended_action": f"Review the {count:,} IQR-flagged rows in `{column}` and document whether they are valid extremes or data-quality errors.",
                "data_justification": f"IQR profiling identified {count:,} outlier values in `{column}`.",
                "business_reason": "Unreviewed extremes can disproportionately influence averages, forecasts, thresholds, and resource planning.",
            })
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
    relationships = non_graphical.get("multivariate", {}).get("strongest_numeric_relationships", [])
    if relationships:
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
    return actions[:4]


def markdown_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> str:
    eda = metrics.get('exploratory_data_analysis', metrics)
    non_graphical = eda.get('non_graphical', eda) if isinstance(eda, dict) else {}
    suggestions = build_datasnap_suggestions(metrics)
    actions = build_strategic_recommendations(metrics)

    num_profiles = non_graphical.get('numeric_summary', {})
    cat_profiles = non_graphical.get('categorical_summary', {})

    tables = []
    if num_profiles:
        tables.append('### Numerical Feature Summary')
        tables.append('| Feature | Count | Mean | Median | Std | Min | Max | IQR | Outliers |')
        tables.append('| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |')
        for col, p in num_profiles.items():
            tables.append(
                f"| `{col}` | {p.get('count', 0):,} | {_number(p.get('mean'))} | {_number(p.get('median'))} | {_number(p.get('std'))} | {_number(p.get('min'))} | {_number(p.get('max'))} | {_number(p.get('iqr'))} | {p.get('outlier_count_iqr', 0):,} |"
            )
        tables.append('')

    if cat_profiles:
        tables.append('### Categorical Feature Summary')
        tables.append('| Feature | Unique | Missing | Cardinality Ratio | Top Categories |')
        tables.append('| :--- | :--- | :--- | :--- | :--- |')
        for col, p in cat_profiles.items():
            top_vals = ", ".join(f"{v['value']} ({v['count']:,})" for v in p.get('top_values', [])[:3])
            tables.append(
                f"| `{col}` | {p.get('unique', 0):,} | {p.get('missing', 0):,} | {_number(p.get('cardinality_ratio'))} | {top_vals} |"
            )
        tables.append('')

    lines = [
        '# Exploratory Data Analysis Report',
        '',
        '## Scope',
        'EDA is a comprehensive methodology that includes both non-graphical statistical summaries and data visualization techniques.',
        '',
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
    ]
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
        '## Verified EDA Output',
        f"```json\n{json.dumps(eda, indent=2, default=str)}\n```",
        '',
        '## Non-Graphical Statistical Summaries',
        *tables,
        'The verified JSON above contains the complete non-graphical statistical output.',
        '',
        '## Data Visualizations',
    ])
    lines.extend(f'### Visualization {index}\n![Visualization {index}](data:image/png;base64,{chart})' for index, chart in enumerate(charts, 1))
    lines.extend([
        '',
        '## Suggestion by DataSnap',
        'The following are conservative next steps based only on the observed EDA results:',
        *[f'- {suggestion}' for suggestion in suggestions],
    ])
    return '\n'.join(lines)


def html_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> str:
    chart_markup = _chart_gallery(charts)
    suggestion_markup = ''.join(f'<li>{_text(suggestion)}</li>' for suggestion in build_datasnap_suggestions(metrics))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Exploratory Data Analysis Report</title>
<style>body{{font:15px/1.6 system-ui;max-width:1000px;margin:40px auto;padding:0 20px;color:#18202a}}pre{{overflow:auto;background:#f3f5f9;padding:16px;border-radius:8px}}.chart-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}}.chart img{{width:100%}}@media(max-width:700px){{.chart-grid{{grid-template-columns:1fr}}}}</style></head>
<body><h1>Exploratory Data Analysis Report</h1>
<p>EDA is a comprehensive methodology that includes both non-graphical statistical summaries and data visualization techniques.</p>
<h2>Univariate Analysis</h2><p>Independent feature profiles include distributions, missingness, cardinality, quantiles, skewness, kurtosis, and IQR outliers.</p>
<h2>Bivariate Analysis</h2><p>Numeric pairs include Pearson and Spearman relationships; categorical-numeric pairs include group counts, means, and medians.</p>
<h2>Multivariate Analysis</h2><p>Numeric features include a Pearson correlation matrix and strongest pairwise relationships.</p>
<h2>1. Data Quality &amp; Distribution Summary</h2>{_metric_sections(metrics)}
<h2>2. Statistical Core Discoveries</h2><p>Skewness, kurtosis, Pearson/Spearman relationships, ANOVA or Welch t-tests, and Chi-square tests are included when valid.</p>
<h2>3. Mandatory Next Actions &amp; Strategic Recommendations</h2><ul>{''.join(f"<li><strong>{_text(action['title'])}:</strong> {_text(action['recommended_action'])}<br><strong>Data Justification:</strong> {_text(action['data_justification'])}<br><strong>Business Reason:</strong> {_text(action['business_reason'])}</li>" for action in build_strategic_recommendations(metrics))}</ul>
<h2>Verified EDA Output</h2>{_metric_sections(metrics)}
<h2>Data Visualizations</h2>{chart_markup}
<h2>Suggestion by DataSnap</h2><p>The following are conservative next steps based only on the observed EDA results:</p><ul>{suggestion_markup}</ul></body></html>"""


def build_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> tuple[str, str]:
    return markdown_report(synthesis, metrics, charts), html_report(synthesis, metrics, charts)
