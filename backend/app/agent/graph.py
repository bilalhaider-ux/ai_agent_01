"""LangGraph StateGraph assembly for Data Analytics AI Agent."""

from typing import Literal
from langgraph.graph import StateGraph, START, END

from .state import AgentState
from .config import AgentConfig
from .nodes import (
    stage1_context_minification,
    stage2_intent_and_plan,
    stage3_sandboxed_code_generation,
    stage4_isolated_execution,
    stage5_self_correction,
    stage6_output_synthesis,
    fatal_execution_error_node,
)


def route_execution(state: AgentState) -> Literal["output_synthesis", "self_correction"]:
    """Conditional router based on execution success."""
    exec_result = state.get("execution_result", {})
    if exec_result.get("success", False):
        return "output_synthesis"
    return "self_correction"


def route_retry(state: AgentState) -> Literal["code_generation", "fatal_error"]:
    """Conditional router based on retry limit budget."""
    cfg = AgentConfig()
    retry_count = state.get("retry_count", 0)
    if retry_count < cfg.max_retries:
        return "code_generation"
    return "fatal_error"


def build_data_agent_graph() -> StateGraph:
    """Construct and compile the 6-stage cyclic LangGraph agent."""
    builder = StateGraph(AgentState)
    
    # Register Nodes
    builder.add_node("minification", stage1_context_minification)
    builder.add_node("intent_plan", stage2_intent_and_plan)
    builder.add_node("code_generation", stage3_sandboxed_code_generation)
    builder.add_node("isolated_execution", stage4_isolated_execution)
    builder.add_node("self_correction", stage5_self_correction)
    builder.add_node("output_synthesis", stage6_output_synthesis)
    builder.add_node("fatal_error", fatal_execution_error_node)
    
    # Edges
    builder.add_edge(START, "minification")
    builder.add_edge("minification", "intent_plan")
    builder.add_edge("intent_plan", "code_generation")
    builder.add_edge("code_generation", "isolated_execution")
    
    # Conditional edge 1: Execution success check
    builder.add_conditional_edges(
        "isolated_execution",
        route_execution,
        {
            "output_synthesis": "output_synthesis",
            "self_correction": "self_correction",
        }
    )
    
    # Conditional edge 2: Retry budget check
    builder.add_conditional_edges(
        "self_correction",
        route_retry,
        {
            "code_generation": "code_generation",
            "fatal_error": "fatal_error",
        }
    )
    
    builder.add_edge("output_synthesis", END)
    builder.add_edge("fatal_error", END)
    
    return builder.compile()

