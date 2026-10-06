"""CLI entrypoint for running the LangGraph Data Analytics AI Agent."""

import os
import sys
import argparse
from pathlib import Path

from .config import AgentConfig
from .graph import build_data_agent_graph


# Ensure Windows console supports UTF-8 characters cleanly
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_agent(
    dataset_path: str,
    query: str,
    provider: str = "ollama",
    model: str = None,
    output_path: str = "decision_ready_artifact.md",
    html_export: bool = True
):
    """Execute the end-to-end agent workflow."""
    # Set runtime provider overrides
    os.environ["LLM_PROVIDER"] = provider
    if model:
        if provider == "mistral":
            os.environ["MISTRAL_MODEL"] = model
        elif provider == "gemini":
            os.environ["GEMINI_MODEL"] = model
        elif provider == "openai":
            os.environ["OPENAI_MODEL"] = model
        else:
            os.environ["OLLAMA_MODEL"] = model
            
    print("=" * 70)
    print(">> STARTING AUTONOMOUS DATA ANALYTICS AI AGENT (LANGGRAPH)")
    print(f"   Dataset:  {dataset_path}")
    print(f"   Query:    {query}")
    print(f"   Provider: {provider.upper()} ({model or 'default model'})")
    print("=" * 70)
    
    app = build_data_agent_graph()
    
    initial_state = {
        "query": query,
        "dataset_path": dataset_path,
        "retry_count": 0
    }
    
    final_state = None
    step_num = 1
    
    # Stream node executions for live transparency
    for output in app.stream(initial_state):
        for node_name, node_output in output.items():
            print(f"\n[Step {step_num}] Node: '{node_name}' finished.")
            
            if node_name == "minification":
                ctx = node_output.get("minified_context", {})
                print(f"   -> Minified Context: {ctx.get('row_count')} rows, {ctx.get('column_count')} columns profiled.")
            elif node_name == "intent_plan":
                plan = node_output.get("plan", {})
                print(f"   -> Intent: {plan.get('primary_intent')}")
                print(f"   -> Formulated Hypotheses: {len(plan.get('hypotheses', []))}")
            elif node_name == "code_generation":
                print("   -> Python script generated targeting Polars/SciPy/Matplotlib.")
            elif node_name == "isolated_execution":
                res = node_output.get("execution_result", {})
                success = res.get("success", False)
                print(f"   -> Subprocess Execution Success: {success}")
                if not success:
                    print(f"   -> Error: {res.get('error_message')}")
            elif node_name == "self_correction":
                retries = node_output.get("retry_count", 0)
                print(f"   -> Self-Correction Triggered (Retry Attempt {retries}/3). Feeding traceback to Code Generator.")
            elif node_name == "output_synthesis":
                print("   -> Synthesizing executive report & embedding visualizations.")
            elif node_name == "fatal_error":
                print(f"   -> [FATAL ERROR] {node_output.get('fatal_error')}")
                
            step_num += 1
            final_state = node_output
            
    if not final_state:
        print("[ERROR] Agent finished without returning state.")
        return
        
    synthesis = final_state.get("synthesis")
    if synthesis:
        report_content = synthesis.get("full_markdown_report", "")
        out_file = Path(output_path)
        out_file.write_text(report_content, encoding="utf-8")
        print(f"\n[OK] Decision-ready report saved to: {out_file.resolve()}")
        
        if html_export:
            html_path = out_file.with_suffix(".html")
            
            # Simple conversion of markdown headers and images to rich HTML
            body_html = report_content
            import html
            import re
            
            # Replace markdown images ![Alt](data:image/png;base64,...) with <img> tags
            body_html = re.sub(
                r'!\[(.*?)\]\((data:image\/png;base64,[^\)]+)\)',
                r'<div class="chart-box"><h4>\1</h4><img src="\2" alt="\1" /></div>',
                body_html
            )
            
            # Format markdown headers
            body_html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', body_html, flags=re.MULTILINE)
            body_html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', body_html, flags=re.MULTILINE)
            body_html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', body_html, flags=re.MULTILINE)
            body_html = re.sub(r'^- (.*?)$', r'<li>\1</li>', body_html, flags=re.MULTILINE)
            body_html = re.sub(r'(<li>.*?</li>)+', r'<ul>\g<0></ul>', body_html, flags=re.DOTALL)
            
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>DataSnap · Decision Report</title>
    <style>
        :root {{ --ink:#11141c; --muted:#767c8b; --line:#e7eaf1; --soft:#f3f5f9; --brand:#4f46e5; --brand-hot:#7c3aed; }}
        * {{ box-sizing:border-box; }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
            max-width: 900px; margin: 0 auto; padding: 40px 24px 64px;
            line-height: 1.6; color: var(--ink); background: #f7f8fb;
        }}
        .brand {{ display:flex; align-items:center; gap:8px; font-weight:700; font-size:14px; }}
        .brand .dot {{ width:9px; height:9px; border-radius:3px; background:linear-gradient(135deg,var(--brand),var(--brand-hot)); }}
        .badge {{ display:inline-block; padding:5px 11px; background:#eef0ff; color:var(--brand); border-radius:999px; font-size:12px; font-weight:600; margin:14px 0 8px; }}
        h1 {{ font-size:30px; letter-spacing:-.02em; margin:4px 0 20px; border-bottom:1px solid var(--line); padding-bottom:.4em; }}
        h2 {{ font-size:18px; margin-top:28px; }}
        h3 {{ font-size:13px; color:#4a4f5c; margin-top:18px; }}
        .chart-box {{ margin:22px 0; text-align:center; background:#fff; padding:16px; border-radius:12px; border:1px solid var(--line); }}
        img {{ max-width:100%; height:auto; border-radius:8px; }}
        ul {{ padding-left:20px; margin:12px 0; }}
        li {{ margin-bottom:6px; }}
        footer {{ margin-top:36px; padding-top:18px; border-top:1px solid var(--line); color:var(--muted); font-size:12px; }}
    </style>
</head>
<body>
    <div class="brand"><span class="dot"></span>DataSnap</div>
    <div class="badge">DECISION BRIEF</div>
    {body_html}
    <footer>Generated by DataSnap · Evidence-first reporting</footer>
</body>
</html>"""
            html_path.write_text(html_content, encoding="utf-8")
            print(f"[OK] Interactive HTML report saved to: {html_path.resolve()}")
            
        print("\n" + "=" * 70)
        print("EXECUTIVE SUMMARY:")
        print(synthesis.get("executive_summary"))
        print("=" * 70)
    elif final_state.get("fatal_error"):
        print("\n[ERROR] AGENT TERMINATED WITH FATAL ERROR:")
        print(final_state.get("fatal_error"))


def main():
    parser = argparse.ArgumentParser(description="Autonomous Data Analytics AI Agent (LangGraph)")
    parser.add_argument("--dataset", type=str, default="backend/data/sample_sales_data.csv", help="Path to CSV or Parquet file")
    parser.add_argument("--query", type=str, default="Analyze product category revenue and customer rating correlation with returns", help="Analytical question")
    parser.add_argument("--provider", type=str, choices=["mistral", "gemini", "ollama", "openai", "mock"], default=None, help="LLM Provider")
    parser.add_argument("--model", type=str, default=None, help="LLM Model name")
    parser.add_argument("--output", type=str, default="decision_ready_artifact.md", help="Output artifact path")
    parser.add_argument("--no-html", action="store_true", help="Disable HTML report export")
    
    args = parser.parse_args()
    
    cfg = AgentConfig()
    selected_provider = args.provider or cfg.provider
    
    run_agent(
        dataset_path=args.dataset,
        query=args.query,
        provider=selected_provider,
        model=args.model,
        output_path=args.output,
        html_export=not args.no_html
    )


if __name__ == "__main__":
    main()

