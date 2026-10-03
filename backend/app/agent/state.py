"""LangGraph State definition for the autonomous agent workflow."""

from typing import TypedDict, Optional, Dict, Any


class AgentState(TypedDict, total=False):
    """Unified state tracking throughout the LangGraph lifecycle."""
    # User Inputs
    query: str
    dataset_path: str
    provider: Optional[str]
    model: Optional[str]
    
    # Stage 1: Context Minification
    minified_context: Optional[Dict[str, Any]]
    data_quality: Optional[Dict[str, Any]]
    
    # Stage 2: Intent & Plan Contract
    plan: Optional[Dict[str, Any]]
    
    # Stage 3: Sandboxed Code Generation
    generated_code: Optional[str]
    
    # Stage 4: Isolated Execution Runtime
    execution_result: Optional[Dict[str, Any]]
    
    # Stage 5: Self-Correction Loop telemetry
    retry_count: int
    error_traceback: Optional[str]
    
    # Stage 6: Output Synthesis
    synthesis: Optional[Dict[str, Any]]
    
    # Terminal Status
    fatal_error: Optional[str]
    status: str

