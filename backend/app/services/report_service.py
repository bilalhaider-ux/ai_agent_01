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


def _bullet_list(items: list[str] | None, empty: str) -> str:
    if not items:
        return f'<p class="muted">{_text(empty)}</p>'
    return '<ul class="clean-list">' + ''.join(f'<li>{_text(item)}</li>' for item in items) + '</ul>'


def markdown_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> str:
    lines = [
        '# Analytical Decision Report',
        '',
        '## Executive Summary',
        synthesis.get('executive_summary', 'No executive summary was returned.'),
        '',
        '## Core Findings & Answers to Query',
        synthesis.get('answers_to_query', 'No direct answer was returned.'),
        '',
        '## Statistical Insights',
    ]
    lines.extend(f'- {item}' for item in synthesis.get('statistical_insights', []))
    lines += ['', '## Recommended Actions']
    lines.extend(f'- {item}' for item in synthesis.get('recommended_actions', []))
    lines += ['', '## Machine-Verified Metrics']
    lines.extend(f'- **{key}:** `{json.dumps(value, default=str) if isinstance(value, (dict, list)) else value}`' for key, value in metrics.items())
    if charts:
        lines += ['', '## Visual Evidence']
        lines.extend(f'### Visualization {index}\n![Visualization {index}](data:image/png;base64,{chart})' for index, chart in enumerate(charts, 1))
    lines += ['', '## Decision Safety Notes', '- Narrative findings and recommendations are advisory.', '- Correlation and statistical significance do not prove causation.', '- Missing values are not zero and unsupported claims remain unknown.']
    return '\n'.join(lines)


def html_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> str:
    executive = _text(synthesis.get('executive_summary', 'No executive summary was returned.'))
    answer = _text(synthesis.get('answers_to_query', 'No direct answer was returned.'))
    insights = _bullet_list(synthesis.get('statistical_insights'), 'No statistical insights were returned.')
    actions = _bullet_list(synthesis.get('recommended_actions'), 'No recommendations were returned.')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Analytical Decision Report</title>
<style>
:root{{--ink:#17283d;--muted:#6e7f93;--line:#dfe7ef;--soft:#f4f8fb;--mint:#159979;--mint-soft:#e7f8f2;--navy:#0b1b2e}}
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fa;color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.shell{{max-width:1180px;margin:auto;padding:42px 28px 70px}}.masthead{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;padding-bottom:32px;border-bottom:1px solid var(--line)}}.eyebrow{{color:var(--mint);font-size:11px;font-weight:800;letter-spacing:.16em}}h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;line-height:1.2}}h1{{font-size:42px;margin:10px 0 8px;letter-spacing:-.03em}}h2{{font-size:25px;margin:0 0 18px}}h3{{font-size:17px;margin:0 0 12px}}.sub{{color:var(--muted);max-width:690px;margin:0}}.badge{{background:var(--mint-soft);border:1px solid #bfe9da;color:#147d65;padding:8px 12px;border-radius:999px;font-size:12px;font-weight:700;white-space:nowrap}}.section{{margin-top:36px}}.summary-grid{{display:grid;grid-template-columns:1.35fr .65fr;gap:18px}}.card{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:25px;box-shadow:0 8px 25px rgba(22,43,65,.04)}}.summary{{font-size:18px;line-height:1.65}}.answer{{margin-top:22px;background:var(--navy);color:#eef8f6;border-radius:8px;padding:20px 22px}}.answer strong{{color:#78e0c1;display:block;font-size:11px;letter-spacing:.12em;margin-bottom:8px}}.answer p{{margin:0}}.stat-card{{display:flex;flex-direction:column;justify-content:space-between}}.stat-card strong{{font-size:33px;color:var(--mint);font-family:Georgia,serif}}.stat-card span{{color:var(--muted);font-size:12px}}.clean-list{{padding:0;margin:0;list-style:none;display:grid;gap:10px}}.clean-list li{{padding-left:19px;position:relative}}.clean-list li:before{{content:"";position:absolute;left:0;top:.7em;width:7px;height:7px;border-radius:50%;background:var(--mint)}}.metric-section{{margin-top:22px}}.metric-section h3{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;font-weight:700;color:#476078}}.table-scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);font-size:13px}}th{{background:var(--navy);color:#e9f5f2;text-align:left;font-size:11px;letter-spacing:.04em;text-transform:uppercase}}th,td{{padding:11px 13px;border-bottom:1px solid var(--line);white-space:nowrap}}tr:last-child td{{border-bottom:0}}td{{color:#40566d}}.chart-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}}.chart{{margin:0;background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px}}.chart img{{display:block;width:100%;height:auto;border-radius:6px}}figcaption{{color:var(--muted);font-size:12px;padding:10px 4px 2px}}.json-block{{overflow:auto;background:var(--soft);border:1px solid var(--line);padding:16px;border-radius:7px;color:#40566d;font-size:12px}}.muted{{color:var(--muted)}}.safety{{background:#fffaf0;border:1px solid #f1dfb2;border-radius:9px;padding:20px;color:#6e5b35}}footer{{margin-top:45px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}}
@media(max-width:760px){{.shell{{padding:26px 16px 50px}}.masthead,.summary-grid{{display:block}}.badge{{display:inline-block;margin-top:18px}}h1{{font-size:33px}}.card{{padding:19px;margin-top:15px}}.chart-grid{{grid-template-columns:1fr}}}}
</style></head><body><main class="shell">
<header class="masthead"><div><div class="eyebrow">LUMEN ANALYTICS · DECISION BRIEF</div><h1>Analytical Decision Report</h1><p class="sub">A machine-assisted analysis prepared from the uploaded dataset. Use verified metrics for decisions and review recommendations before acting.</p></div><div class="badge">Verified metrics</div></header>
<section class="section summary-grid"><article class="card"><h2>Executive Summary</h2><p class="summary">{executive}</p><div class="answer"><strong>ANSWER TO YOUR QUESTION</strong><p>{answer}</p></div></article><aside class="card stat-card"><div><div class="eyebrow">REPORT STATUS</div><strong>Ready</strong></div><span>Machine-verified evidence attached<br>Human review required</span></aside></section>
<section class="section card"><h2>Statistical Insights</h2>{insights}</section>
<section class="section card"><h2>Recommended Actions</h2>{actions}</section>
<section class="section"><h2>Visual Evidence</h2>{_chart_gallery(charts)}</section>
<section class="section card"><h2>Machine-Verified Metrics</h2>{_metric_sections(metrics)}</section>
<section class="section safety"><strong>Decision safety</strong><p>Narrative findings are advisory. Correlation and statistical significance do not prove causation. Missing values are not zero, and unsupported claims remain unknown.</p></section>
<footer>Generated by Lumen Analytics · Evidence-first reporting</footer></main></body></html>'''


def build_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> tuple[str, str]:
    return markdown_report(synthesis, metrics, charts), html_report(synthesis, metrics, charts)
