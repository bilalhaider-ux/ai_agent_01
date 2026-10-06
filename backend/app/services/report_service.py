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


def markdown_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> str:
    eda = metrics.get('exploratory_data_analysis', metrics)
    suggestions = build_datasnap_suggestions(metrics)
    lines = [
        '# Exploratory Data Analysis Report',
        '',
        '## Scope',
        'EDA is a comprehensive methodology that includes both non-graphical statistical summaries and data visualization techniques.',
        '',
        '## Non-Graphical Statistical Summaries',
        f"```json\n{json.dumps(eda, indent=2, default=str)}\n```",
        '',
        '## Data Visualizations',
    ]
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
<h2>Non-Graphical Statistical Summaries</h2>{_metric_sections(metrics)}
<h2>Data Visualizations</h2>{chart_markup}
<h2>Suggestion by DataSnap</h2><p>The following are conservative next steps based only on the observed EDA results:</p><ul>{suggestion_markup}</ul></body></html>"""


def build_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> tuple[str, str]:
    return markdown_report(synthesis, metrics, charts), html_report(synthesis, metrics, charts)
