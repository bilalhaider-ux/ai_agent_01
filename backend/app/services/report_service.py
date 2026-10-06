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
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DataSnap · Decision Report</title>
<style>
:root{{--ink:#11141c;--muted:#767c8b;--line:#e7eaf1;--soft:#f3f5f9;--brand:#4f46e5;--brand-hot:#7c3aed;--brand-soft:#eef0ff;--ok:#0f9d6b;--ok-soft:#e4f6ee}}
*{{box-sizing:border-box}}body{{margin:0;background:#f7f8fb;color:var(--ink);font:15px/1.6 'Inter',system-ui,-apple-system,"Segoe UI",sans-serif}}.shell{{max-width:900px;margin:auto;padding:40px 24px 64px}}
header{{padding-bottom:24px;border-bottom:1px solid var(--line);margin-bottom:8px}}.brand{{display:flex;align-items:center;gap:8px;font-weight:700;font-size:14px;letter-spacing:-.01em}}.brand .dot{{width:9px;height:9px;border-radius:3px;background:linear-gradient(135deg,var(--brand),var(--brand-hot))}}.eyebrow{{color:var(--brand);font-size:11px;font-weight:700;letter-spacing:.14em;margin-top:18px}}h1{{font-size:30px;margin:6px 0 8px;letter-spacing:-.02em;line-height:1.2}}h2{{font-size:18px;margin:0 0 14px;letter-spacing:-.01em}}h3{{font-size:13px;margin:0 0 10px;color:#4a4f5c}}.sub{{color:var(--muted);max-width:640px;margin:0}}
.badge{{display:inline-block;background:var(--ok-soft);color:var(--ok);padding:5px 11px;border-radius:999px;font-size:12px;font-weight:600;margin-top:14px}}
.section{{margin-top:28px}}.card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:22px}}.summary{{margin:0;line-height:1.65}}
.answer{{margin-top:18px;background:var(--brand-soft);border:1px solid #c7cbff;border-radius:10px;padding:16px 18px}}.answer strong{{color:var(--brand);display:block;font-size:11px;letter-spacing:.1em;margin-bottom:6px}}.answer p{{margin:0}}
.clean-list{{padding:0;margin:0;list-style:none;display:grid;gap:9px}}.clean-list li{{padding-left:18px;position:relative}}.clean-list li:before{{content:"";position:absolute;left:0;top:.65em;width:6px;height:6px;border-radius:50%;background:var(--brand)}}
.metric-section{{margin-top:18px}}.metric-section:first-child{{margin-top:0}}.table-scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:13px}}th{{background:var(--soft);color:#4a4f5c;text-align:left;font-size:11px;letter-spacing:.03em;text-transform:uppercase}}th,td{{padding:9px 12px;border-bottom:1px solid var(--line);white-space:nowrap}}tr:last-child td{{border-bottom:0}}td{{color:#4a4f5c}}
.chart-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}}.chart{{margin:0;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px}}.chart img{{display:block;width:100%;height:auto;border-radius:7px}}figcaption{{color:var(--muted);font-size:12px;padding:9px 2px 2px}}
.json-block{{overflow:auto;background:var(--soft);border:1px solid var(--line);padding:14px;border-radius:9px;color:#4a4f5c;font:12px/1.5 'JetBrains Mono',ui-monospace,monospace}}.metric-value{{margin:0;font:600 22px 'JetBrains Mono',ui-monospace,monospace;color:var(--brand)}}.muted{{color:var(--muted)}}
.safety{{background:#fff8ec;border:1px solid #f3e2bd;border-radius:10px;padding:16px 18px;color:#7a6329;font-size:13px}}.safety strong{{display:block;margin-bottom:4px}}
footer{{margin-top:36px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}}
@media(max-width:720px){{.shell{{padding:26px 16px 48px}}h1{{font-size:25px}}.chart-grid{{grid-template-columns:1fr}}}}
</style></head><body><main class="shell">
<header><div class="brand"><span class="dot"></span>DataSnap</div><div class="eyebrow">DECISION BRIEF</div><h1>Analytical Decision Report</h1><p class="sub">A machine-assisted analysis prepared from the uploaded dataset. Use verified metrics for decisions and review recommendations before acting.</p><span class="badge">Verified metrics · Human review required</span></header>
<section class="section card"><h2>Executive Summary</h2><p class="summary">{executive}</p><div class="answer"><strong>ANSWER TO YOUR QUESTION</strong><p>{answer}</p></div></section>
<section class="section card"><h2>Statistical Insights</h2>{insights}</section>
<section class="section card"><h2>Recommended Actions</h2>{actions}</section>
<section class="section"><h2>Visual Evidence</h2>{_chart_gallery(charts)}</section>
<section class="section card"><h2>Machine-Verified Metrics</h2>{_metric_sections(metrics)}</section>
<section class="section safety"><strong>Decision safety</strong>Narrative findings are advisory. Correlation and statistical significance do not prove causation. Missing values are not zero, and unsupported claims remain unknown.</section>
<footer>Generated by DataSnap · Evidence-first reporting</footer></main></body></html>'''


def build_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> tuple[str, str]:
    return markdown_report(synthesis, metrics, charts), html_report(synthesis, metrics, charts)
