"""Offline Mock Chat Model for validation, benchmarking, and local testing.

Emulates intelligent Chief Data Scientist reasoning, Polars/SciPy/Matplotlib
code generation, and executive synthesis without external network or LLM dependencies.
"""

from typing import Any, List, Optional
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableLambda

from .contracts import AnalyticalPlan, OutputSynthesis


class MockAnalyticsChatModel(SimpleChatModel):
    """Mock LLM returning deterministic, schema-compliant responses for all stages."""
    
    @property
    def _llm_type(self) -> str:
        return "mock-analytics-llm"
        
    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> str:
        combined = " ".join([m.content if hasattr(m, "content") else str(m) for m in messages])
        
        # Check for Stage 3: Code Generation
        if "EXECUTION ENVIRONMENT CONTRACT" in combined or "Write the complete Python code" in combined:
            return '''
import polars as pl
from pathlib import Path
import matplotlib.pyplot as plt
from scipy import stats

# Read supported dataset formats using Polars
dataset_suffix = Path(DATASET_PATH).suffix.lower()
if dataset_suffix == ".xlsx":
    df = pl.read_excel(DATASET_PATH)
elif dataset_suffix == ".parquet":
    df = pl.read_parquet(DATASET_PATH)
elif dataset_suffix == ".tsv":
    df = pl.read_csv(DATASET_PATH, separator="\\t")
elif dataset_suffix == ".jsonl":
    df = pl.read_ndjson(DATASET_PATH)
else:
    df = pl.read_json(DATASET_PATH) if dataset_suffix == ".json" else pl.read_csv(DATASET_PATH)

# Clean and filter null values
valid_df = df.filter(pl.col("product_category").is_not_null() & pl.col("total_revenue").is_not_null())

# Group-by category aggregations
category_summary = (
    valid_df.group_by("product_category")
    .agg([
        pl.col("total_revenue").sum().alias("total_revenue"),
        pl.col("total_revenue").mean().alias("avg_revenue"),
        pl.col("customer_rating").mean().alias("avg_rating"),
        pl.col("units_sold").sum().alias("total_units")
    ])
    .sort("total_revenue", descending=True)
)

# Statistical Correlation using SciPy (Rating vs Revenue)
corr_coef, p_value = stats.pearsonr(
    valid_df["customer_rating"].to_numpy(),
    valid_df["total_revenue"].to_numpy()
)

# Return rate calculation
returns_count = df.filter(pl.col("returned") == "Yes").height
return_rate = (returns_count / df.height) * 100

# Populate metrics output contract
__AGENT_OUTPUT__["metrics"] = {
    "overall_total_revenue": float(valid_df["total_revenue"].sum()),
    "avg_customer_rating": round(float(valid_df["customer_rating"].mean()), 2),
    "pearson_correlation_rating_vs_revenue": round(float(corr_coef), 4),
    "correlation_p_value": round(float(p_value), 6),
    "overall_return_rate_pct": round(float(return_rate), 2),
    "top_category": category_summary["product_category"][0],
    "category_revenue_distribution": dict(
        zip(category_summary["product_category"].to_list(), [round(x, 2) for x in category_summary["total_revenue"].to_list()])
    )
}

# Visualization 1: Total Revenue by Product Category
plt.figure(figsize=(8, 5))
categories = category_summary["product_category"].to_list()
revenues = category_summary["total_revenue"].to_list()
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
bars = plt.bar(categories, revenues, color=colors[:len(categories)], edgecolor='black', alpha=0.85)
plt.title("Total Revenue by Product Category", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Product Category", fontsize=11)
plt.ylabel("Total Revenue ($)", fontsize=11)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.xticks(rotation=25)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 50, f"${yval:,.0f}", ha='center', va='bottom', fontsize=9)
save_current_figure_to_base64()

# Visualization 2: Customer Rating vs Revenue Scatter with Trendline
plt.figure(figsize=(8, 5))
ratings = valid_df["customer_rating"].to_numpy()
revs = valid_df["total_revenue"].to_numpy()
plt.scatter(ratings, revs, color='darkorange', edgecolors='black', s=70, alpha=0.8)
# Add linear regression fit line
slope, intercept, _, _, _ = stats.linregress(ratings, revs)
plt.plot(ratings, slope * ratings + intercept, color='navy', linestyle='--', linewidth=2, label=f"Trend (r = {corr_coef:.2f})")
plt.title("Customer Rating vs. Order Revenue", fontsize=14, fontweight='bold', pad=12)
plt.xlabel("Customer Rating (1 - 5 Stars)", fontsize=11)
plt.ylabel("Order Revenue ($)", fontsize=11)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
save_current_figure_to_base64()

__AGENT_OUTPUT__["summary"] = "Computed category revenue breakdown and Pearson correlation between ratings and order values."
'''

        # Stage 6: Output Synthesis
        elif "Produce an executive decision-ready artifact" in combined:
            return """# Executive Summary
The empirical analysis of retail transactions reveals Electronics as the primary revenue driver, generating substantial sales volume with strong transaction margins. Statistical correlation tests between customer satisfaction and order revenue indicate a positive relationship, while returns cluster predominantly within fashion and discounted home goods.

## Key Statistical Insights
- Electronics achieved top total revenue with premium average order value.
- Pearson correlation test indicates significant correlation between customer rating and purchase size.
- Product return rate is concentrated in high-discount apparel categories.

## Strategic Recommendations
1. Scale inventory and targeted marketing for high-margin Electronics.
2. Investigate sizing and expectation mismatch in Fashion categories to curb return rates.
3. Align promotional discounts with categories having high satisfaction retention.
"""

        # Stage 2: Intent & Planning
        else:
            return """{
  "primary_intent": "Analyze product category revenue distribution and customer rating correlation with returns",
  "hypotheses": [
    "Electronics and Beauty categories generate higher average revenue per transaction.",
    "Higher customer satisfaction ratings correlate positively with order revenue and negatively with returns."
  ],
  "data_transformations": [
    "Filter null values in categorical columns",
    "Group by product_category and compute sum and average revenue, units sold, and mean rating",
    "Compute total return rates across all orders"
  ],
  "statistical_methods": [
    "Pearson correlation coefficient between customer_rating and total_revenue via scipy.stats.pearsonr",
    "Two-sample difference analysis across returned and non-returned order ratings"
  ],
  "visualization_plan": [
    "Bar chart of Total Revenue by Product Category with data labels",
    "Scatter plot with linear regression trendline of Customer Rating vs Order Revenue"
  ],
  "required_metrics": [
    "overall_total_revenue",
    "avg_customer_rating",
    "pearson_correlation_rating_vs_revenue",
    "overall_return_rate_pct",
    "category_revenue_distribution"
  ]
}"""

    def with_structured_output(self, schema: Any, **kwargs: Any):
        """Mock structured output parser returning Pydantic schema instances."""
        def _parse(messages: List[BaseMessage]):
            raw_text = self._call(messages)
            if schema == AnalyticalPlan:
                return AnalyticalPlan(
                    primary_intent="Analyze product category revenue and customer rating correlation with returns",
                    hypotheses=[
                        "Electronics and Beauty categories generate higher average revenue per transaction.",
                        "Higher customer satisfaction ratings correlate positively with order revenue and negatively with returns."
                    ],
                    data_transformations=[
                        "Filter null values in categorical columns",
                        "Group by product_category and aggregate total revenue and ratings",
                        "Calculate return rates by category"
                    ],
                    statistical_methods=[
                        "scipy.stats.pearsonr between customer rating and total revenue",
                        "Descriptive quantiles on order revenues"
                    ],
                    visualization_plan=[
                        "Bar chart: Total Revenue by Product Category",
                        "Scatter plot: Customer Rating vs Revenue with trendline"
                    ],
                    required_metrics=[
                        "overall_total_revenue",
                        "avg_customer_rating",
                        "pearson_correlation_rating_vs_revenue",
                        "overall_return_rate_pct"
                    ]
                )
            elif schema == OutputSynthesis:
                return OutputSynthesis(
                    executive_summary="The analysis of transaction records establishes Electronics as the dominant revenue driver with strong average order values. Customer rating shows a statistically significant positive correlation with revenue volume, while returns are disproportionately concentrated in discounted categories.",
                    statistical_insights=[
                        "Electronics leads category revenues with premium unit margins.",
                        "Statistically significant positive Pearson correlation observed between rating and order revenue.",
                        "Overall return rate is 20.0%, concentrated in high-discount apparel and kitchen transactions."
                    ],
                    answers_to_query="Product revenue is heavily concentrated in Electronics, followed by Sports and Home & Kitchen. Higher customer ratings correspond with larger transaction amounts, and returns occur predominantly in lower-rated transactions.",
                    recommended_actions=[
                        "Expand high-performing Electronics inventory and optimize marketing budget toward top categories.",
                        "Implement stricter quality control and sizing clarity for apparel to reduce return rates.",
                        "Introduce post-purchase follow-ups for transactions with ratings under 4.0 to improve retention."
                    ],
                    full_markdown_report=""
                )
            return schema.model_validate_json(raw_text)
            
        return RunnableLambda(_parse)

