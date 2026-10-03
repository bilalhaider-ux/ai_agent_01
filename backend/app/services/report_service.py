"""Report rendering and short-lived analysis result storage."""

import html
import re
from typing import Any

from app.agent.grounding import append_verified_evidence


def markdown_to_html(markdown: str) -> str:
    body = html.escape(markdown)
    body = re.sub(
        r"!\[(.*?)\]\(data:image/png;base64,([^\)]+)\)",
        r'<img src="data:image/png;base64,\2" alt="\1">',
        body,
    )
    body = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", body, flags=re.MULTILINE)
    body = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", body, flags=re.MULTILINE)
    body = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", body, flags=re.MULTILINE)
    body = re.sub(r"^- (.*?)$", r"<li>\1</li>", body, flags=re.MULTILINE)
    body = re.sub(r"(<li>.*?</li>\n?)+", r"<ul>\g<0></ul>", body)
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Analytical Decision Report</title><style>body{{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;line-height:1.6;color:#202124}}h1{{color:#155eef}}h2{{border-bottom:1px solid #ddd;padding-bottom:.25rem}}img{{max-width:100%;display:block;margin:1rem 0}}</style></head><body>{body}</body></html>"


def build_report(synthesis: dict[str, Any], metrics: dict[str, Any], charts: list[str]) -> tuple[str, str]:
    report = synthesis.get("full_markdown_report", "")
    report += "\n\n## Metrics\n" + "\n".join(f"- **{key}:** {value}" for key, value in metrics.items())
    if charts:
        report += "\n\n## Embedded Visualizations\n" + "\n".join(f"\n### Chart {index}\n![Chart {index}](data:image/png;base64,{chart})" for index, chart in enumerate(charts, 1))
    report = append_verified_evidence(report, metrics)
    return report, markdown_to_html(report)