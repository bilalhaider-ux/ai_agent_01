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
            try:
                try:
                    from app.services.report_service import html_report
                except ImportError:
                    from ..services.report_service import html_report
                execution = final_state.get("execution_result", {})
                html_content = html_report(
                    synthesis=synthesis,
                    metrics=execution.get("metrics", {}),
                    charts=execution.get("base64_charts", []),
                    dataset_name=Path(dataset_path).name,
                )
            except Exception:
                html_content = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>DataSnap EDA Report</title></head><body><h1>DataSnap EDA Report</h1><pre>{report_content}</pre></body></html>"
            html_path.write_text(html_content, encoding="utf-8")
            print(f"\n[OK] Executive DataSnap HTML report saved to: {html_path.resolve()}")
            
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

