"""Unit tests for executive report rendering service."""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.report_service import (
    build_datasnap_suggestions,
    build_report,
    build_strategic_recommendations,
    html_report,
    markdown_report,
)


class TestReportService(unittest.TestCase):
    def setUp(self):
        self.mock_metrics = {
            "exploratory_data_analysis": {
                "non_graphical": {
                    "row_count": 1000,
                    "column_count": 5,
                    "data_health": {
                        "score": 92.5,
                        "grade": "Excellent",
                        "rating_description": "Production and modeling ready.",
                        "sub_scores": {
                            "completeness": 98.0,
                            "uniqueness": 100.0,
                            "outlier_control": 95.0,
                            "type_consistency": 100.0,
                        },
                    },
                    "data_health_score": 92.5,
                    "business_insights": {
                        "pareto_analysis": {
                            "applicable": True,
                            "column": "total_revenue",
                            "is_pareto": True,
                            "top_20_pct_volume_share": 78.4,
                            "pct_records_generating_80_pct": 21.2,
                            "summary": "Top 20% of records account for 78.4% of total total_revenue.",
                        },
                        "missingness_alerts": [
                            {
                                "column": "shipping_cost",
                                "missing_count": 150,
                                "missing_pct": 15.0,
                                "severity": "medium",
                                "recommended_strategy": "Impute with median value.",
                            }
                        ],
                        "ml_readiness": {
                            "multicollinearity_flags": [
                                {
                                    "feature_1": "unit_price",
                                    "feature_2": "total_revenue",
                                    "pearson_r": 0.89,
                                    "recommendation": "Drop one feature to avoid unstable linear coefficients.",
                                }
                            ],
                            "zero_variance_columns": [],
                        },
                    },
                    "numeric_summary": {
                        "total_revenue": {
                            "count": 1000,
                            "mean": 152.3,
                            "median": 120.0,
                            "std": 45.2,
                            "min": 10.0,
                            "max": 850.0,
                            "quantiles": {"q25": 80.0, "q75": 210.0},
                            "iqr": 130.0,
                            "outlier_count_iqr": 12,
                            "skewness": 1.25,
                            "kurtosis": 2.1,
                        }
                    },
                    "categorical_summary": {
                        "category": {
                            "unique": 4,
                            "missing": 0,
                            "cardinality_ratio": 0.004,
                            "top_values": [{"value": "Electronics", "count": 450}],
                        }
                    },
                    "outlier_counts_iqr": {"total_revenue": 12},
                    "missing_counts": {"shipping_cost": 150},
                    "missing_percentages": {"shipping_cost": 15.0},
                    "duplicate_row_count": 0,
                    "statistical_tests": {
                        "categorical_numeric_tests": [
                            {
                                "categorical": "category",
                                "numeric": "total_revenue",
                                "test": "One-way ANOVA",
                                "statistic": 14.52,
                                "p_value": 0.0001,
                                "significant_at_0_05": True,
                            }
                        ]
                    },
                }
            }
        }
        self.mock_synthesis = {
            "executive_summary": "Exploratory analysis confirms strong 80/20 revenue concentration.",
            "statistical_insights": ["High revenue concentration in top tier."],
            "answers_to_query": "Analyze revenue distribution",
        }
        self.mock_charts = ["iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="]

    def test_no_legacy_brand_remnants(self):
        """Verify absolute eradication of legacy brand names in HTML and Markdown."""
        md, html_doc = build_report(
            self.mock_synthesis,
            self.mock_metrics,
            self.mock_charts,
            analysis_id="TEST-123",
            dataset_name="sales.csv",
        )
        self.assertNotIn("lumen", md.lower())
        self.assertNotIn("lumen", html_doc.lower())
        self.assertIn("DataSnap", md)
        self.assertIn("DataSnap", html_doc)

    def test_html_report_executive_features(self):
        """Verify executive styling, print rules, pills, and scorecard in HTML."""
        html_doc = html_report(
            self.mock_synthesis,
            self.mock_metrics,
            self.mock_charts,
            analysis_id="DS-TEST-456",
            dataset_name="enterprise_metrics.csv",
        )
        # Fonts and Branding
        self.assertIn("Onest", html_doc)
        self.assertIn("JetBrains Mono", html_doc)
        self.assertIn("DataSnap", html_doc)
        self.assertIn("DS-TEST-456", html_doc)
        self.assertIn("enterprise_metrics.csv", html_doc)

        # Audit trail pills
        self.assertIn("Verified Polars Execution", html_doc)
        self.assertIn("Deterministic SciPy Engine", html_doc)
        self.assertIn("Zero-Imputation Evidence", html_doc)

        # Health score
        self.assertIn("92.5", html_doc)
        self.assertIn("EXCELLENT", html_doc)

        # A4 Print Rules
        self.assertIn("@media print", html_doc)
        self.assertIn("@page", html_doc)
        self.assertIn("size: A4", html_doc)
        self.assertIn("page-break-inside: avoid", html_doc)

        # Required API test assertions
        self.assertIn("Suggestion by DataSnap", html_doc)
        self.assertIn("<img", html_doc)

    def test_markdown_report_executive_features(self):
        """Verify GitHub callouts, collapsible details, and pipeline checklist."""
        md = markdown_report(
            self.mock_synthesis,
            self.mock_metrics,
            self.mock_charts,
            analysis_id="DS-TEST-789",
            dataset_name="data.csv",
        )
        # Required strings
        self.assertIn("# Exploratory Data Analysis Report", md)
        self.assertIn("## Non-Graphical Statistical Summaries", md)
        self.assertIn("## Data Visualizations", md)
        self.assertIn("## Suggestion by DataSnap", md)

        # Callouts & details
        self.assertIn("> [!NOTE]", md)
        self.assertIn("Deterministic Data Health Score: 92.5/100", md)
        self.assertIn("<details", md)
        self.assertIn("<summary>", md)

        # Actionable checklist
        self.assertIn("Downstream Data Pipeline Actionable Checklist", md)
        self.assertIn("- [ ]", md)

    def test_strategic_recommendations_integration(self):
        """Verify recommendations account for Pareto, multicollinearity, and missingness."""
        actions = build_strategic_recommendations(self.mock_metrics)
        self.assertTrue(len(actions) > 0)
        action_titles = [a["title"].lower() for a in actions]
        # Should include missingness, multicollinearity, or pareto
        has_business_check = any("missing-value" in t or "multicollinearity" in t or "pareto" in t for t in action_titles)
        self.assertTrue(has_business_check)

    def test_empty_and_edge_case_metrics(self):
        """Verify safe rendering when metrics are empty or missing sub-keys."""
        empty_metrics = {}
        empty_synthesis = {}
        md, html_doc = build_report(empty_synthesis, empty_metrics, [])
        self.assertIn("# Exploratory Data Analysis Report", md)
        self.assertIn("DataSnap", html_doc)
        self.assertIn("@media print", html_doc)

    def test_pareto_none_total_volume_and_none_counts(self):
        """Verify robust rendering when total_volume or column counts are None."""
        metrics_with_none_values = {
            "exploratory_data_analysis": {
                "non_graphical": {
                    "row_count": 100,
                    "column_count": 2,
                    "business_insights": {
                        "pareto_analysis": {
                            "applicable": True,
                            "column": "volume_feature",
                            "is_pareto": True,
                            "top_20_pct_volume_share": 75.0,
                            "pct_records_generating_80_pct": 20.0,
                            "total_volume": None,  # Explicitly None to test boundary condition
                        },
                    },
                    "numeric_summary": {
                        "volume_feature": {
                            "count": None,
                            "outlier_count_iqr": None,
                            "mean": None,
                        }
                    },
                    "categorical_summary": {
                        "cat_feature": {
                            "unique": None,
                            "missing": None,
                            "cardinality_ratio": None,
                            "top_values": [{"value": "A", "count": None}],
                        }
                    },
                }
            }
        }
        actions = build_strategic_recommendations(metrics_with_none_values)
        self.assertTrue(len(actions) > 0)
        md, html_doc = build_report(self.mock_synthesis, metrics_with_none_values, [])
        self.assertIn("DataSnap", html_doc)
        self.assertIn("volume_feature", md)
        self.assertIn("cat_feature", html_doc)

    def test_missingness_alerts_in_html_and_markdown(self):
        """Verify high-risk missingness alerts are rendered in HTML alert banner and Markdown callouts."""
        metrics_with_severe_missing = {
            "exploratory_data_analysis": {
                "non_graphical": {
                    "row_count": 500,
                    "column_count": 3,
                    "business_insights": {
                        "missingness_alerts": [
                            {
                                "column": "critical_feature",
                                "missing_count": 350,
                                "missing_pct": 70.0,
                                "severity": "critical",
                                "recommended_strategy": "Drop column (exceeds 50% threshold).",
                            }
                        ],
                        "ml_readiness": {},
                    },
                    "missing_counts": {"critical_feature": 350},
                }
            }
        }
        md = markdown_report(self.mock_synthesis, metrics_with_severe_missing, [])
        html_doc = html_report(self.mock_synthesis, metrics_with_severe_missing, [])

        # Check Markdown
        self.assertIn("> [!WARNING]", md)
        self.assertIn("critical_feature", md)
        self.assertIn("70.0% null values", md)
        self.assertIn("High-Risk Missingness Remediation", md)

        # Check HTML
        self.assertIn("alert-danger", html_doc)
        self.assertIn("High-Risk Missingness (CRITICAL)", html_doc)
        self.assertIn("critical_feature", html_doc)

    def test_print_running_headers_and_table_wrapping(self):
        """Verify CSS paged media margin boxes and print table wrapping overrides."""
        html_doc = html_report(self.mock_synthesis, self.mock_metrics, self.mock_charts)
        self.assertIn("@top-left", html_doc)
        self.assertIn("@top-right", html_doc)
        self.assertIn("@bottom-left", html_doc)
        self.assertIn("@bottom-right", html_doc)
        self.assertIn("white-space: normal", html_doc)
        self.assertIn("font-size: 7.5pt", html_doc)

    def test_chart_details_titles_rendered(self):
        """Verify descriptive chart titles from chart_details appear in HTML and Markdown."""
        chart_details = [
            {"title": "Histogram: total_revenue", "type": "histogram", "feature": "total_revenue"}
        ]
        md = markdown_report(self.mock_synthesis, self.mock_metrics, self.mock_charts, chart_details=chart_details)
        html_doc = html_report(self.mock_synthesis, self.mock_metrics, self.mock_charts, chart_details=chart_details)

        self.assertIn("Histogram: total_revenue", md)
        self.assertIn("Histogram: total_revenue", html_doc)


if __name__ == "__main__":
    unittest.main()
