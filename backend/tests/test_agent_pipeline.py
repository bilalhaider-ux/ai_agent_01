"""Integration and Unit Test Suite for Data Analytics AI Agent.

Tests:
1. Stage 1: Context Minification
2. Stage 4: Isolated Execution Runtime (success case)
3. Stage 4 & 5: Isolated Execution Runtime error handling (failure case)
4. Full StateGraph compilation & edge routing
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent.minifier import minify_dataset
from app.agent.executor import execute_sandboxed_code
from app.agent.graph import build_data_agent_graph, route_execution, route_retry
from app.agent.contracts import DatasetMinifiedContext, ExecutionResult


class TestAgentPipeline(unittest.TestCase):
    def setUp(self):
        self.dataset_path = str(Path(__file__).parent.parent / "data" / "sample_sales_data.csv")

    def test_stage1_context_minification(self):
        """Verify minifier extracts schema, dtypes, nulls, and sample from CSV."""
        context = minify_dataset(self.dataset_path)
        self.assertIsInstance(context, DatasetMinifiedContext)
        self.assertGreater(context.row_count, 0)
        self.assertGreater(context.column_count, 5)
        self.assertIn("total_revenue", context.columns)
        self.assertIn("customer_rating", context.columns)
        self.assertIn("total_revenue", context.dtypes)
        self.assertIn("null_counts", context.model_dump())
        self.assertTrue(len(context.sample_markdown) > 0)
        print("\n[TEST PASS] Stage 1 Context Minification verified.")

    def test_stage4_isolated_execution_success(self):
        """Verify subprocess execution runtime computes metrics and exports charts."""
        code = """
import polars as pl
import matplotlib.pyplot as plt

df = pl.read_csv(DATASET_PATH)

# Aggregation
cat_summary = (
    df.filter(pl.col("product_category").is_not_null())
    .group_by("product_category")
    .agg([
        pl.col("total_revenue").sum().alias("sum_revenue"),
        pl.col("units_sold").sum().alias("sum_units")
    ])
)

# Save metrics into output contract
__AGENT_OUTPUT__["metrics"] = {
    "total_revenue": float(df["total_revenue"].sum()),
    "avg_rating": float(df["customer_rating"].mean()),
    "category_counts": dict(zip(cat_summary["product_category"].to_list(), cat_summary["sum_revenue"].to_list()))
}

# Plot
plt.figure(figsize=(6, 4))
plt.bar(cat_summary["product_category"].to_list(), cat_summary["sum_revenue"].to_list(), color="royalblue")
plt.title("Revenue by Category")
plt.xlabel("Category")
plt.ylabel("Revenue ($)")
plt.xticks(rotation=45)
save_current_figure_to_base64()
"""
        result = execute_sandboxed_code(code, self.dataset_path)
        self.assertTrue(result.success, f"Execution failed: {result.error_message}")
        self.assertIn("total_revenue", result.metrics)
        self.assertGreater(result.metrics["total_revenue"], 0)
        self.assertEqual(len(result.base64_charts), 1)
        self.assertTrue(len(result.base64_charts[0]) > 100)
        print("\n[TEST PASS] Stage 4 Isolated Execution (Success) verified.")

    def test_stage4_and_5_isolated_execution_failure(self):
        """Verify subprocess runtime captures errors cleanly for self-correction."""
        broken_code = """
import polars as pl
# Intentional bug: accessing non-existent column
df = pl.read_csv(DATASET_PATH)
invalid = df["non_existent_column_xyz"].sum()
"""
        result = execute_sandboxed_code(broken_code, self.dataset_path)
        self.assertFalse(result.success)
        self.assertNotEqual(result.return_code, 0)
        self.assertIn("ColumnNotFoundError", result.stderr)
        print("\n[TEST PASS] Stage 4 & 5 Error Traceback Capture verified.")

    def test_graph_compilation_and_routes(self):
        """Verify LangGraph compiles without errors and routing functions work."""
        app = build_data_agent_graph()
        self.assertIsNotNone(app)
        
        # Test route_execution
        self.assertEqual(route_execution({"execution_result": {"success": True}}), "output_synthesis")
        self.assertEqual(route_execution({"execution_result": {"success": False}}), "self_correction")
        
        # Test route_retry
        self.assertEqual(route_retry({"retry_count": 1}), "code_generation")
        self.assertEqual(route_retry({"retry_count": 2}), "code_generation")
        self.assertEqual(route_retry({"retry_count": 3}), "fatal_error")
        print("\n[TEST PASS] Graph Compilation & Routing verified.")

    def test_full_agent_graph_invocation(self):
        """Test full LangGraph StateGraph invocation through all stages."""
        import os
        os.environ["LLM_PROVIDER"] = "mock"
        app = build_data_agent_graph()
        initial_state = {
            "query": "Analyze product category revenue distribution and return rates",
            "dataset_path": self.dataset_path,
            "retry_count": 0
        }
        final_state = app.invoke(initial_state)
        self.assertIn("synthesis", final_state)
        self.assertIn("execution_result", final_state)
        self.assertTrue(final_state["execution_result"]["success"])
        self.assertEqual(final_state["status"], "completed")
        print("\n[TEST PASS] Full LangGraph StateGraph Invocation verified.")


if __name__ == "__main__":
    unittest.main()

