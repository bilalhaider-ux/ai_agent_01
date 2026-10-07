"""Unit tests for deterministic Data Health Score and commercial EDA business checks."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Mock out heavy compiled C-extensions for fast unit testing in any Python runtime
sys.modules["polars"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["scipy.stats"] = MagicMock()
sys.modules["matplotlib"] = MagicMock()
sys.modules["matplotlib.pyplot"] = MagicMock()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.eda import (
    _calculate_data_health_score,
    _missingness_alerts,
    _ml_readiness_warnings,
    _pareto_analysis,
)


class TestEdaBusiness(unittest.TestCase):
    def test_data_health_score_perfect_dataset(self):
        """Verify 100/100 score on flawless data without nulls, duplicates, or zero-variance."""
        mock_df = MagicMock()
        mock_df.height = 100
        mock_df.width = 4
        mock_df.columns = ["feat_a", "feat_b", "cat_a", "cat_b"]

        col_mock = MagicMock()
        col_mock.null_count.return_value = 0
        mock_df.get_column.return_value = col_mock

        numeric = ["feat_a", "feat_b"]
        categorical = ["cat_a", "cat_b"]
        numeric_summary = {
            "feat_a": {"count": 100, "outlier_count_iqr": 0, "std": 12.5, "min": 1.0, "max": 50.0},
            "feat_b": {"count": 100, "outlier_count_iqr": 0, "std": 5.2, "min": 0.5, "max": 20.0},
        }
        categorical_summary = {
            "cat_a": {"unique": 5},
            "cat_b": {"unique": 10},
        }

        health = _calculate_data_health_score(mock_df, numeric, categorical, numeric_summary, categorical_summary, 0)
        self.assertEqual(health["score"], 100.0)
        self.assertEqual(health["grade"], "Excellent")
        self.assertEqual(health["sub_scores"]["completeness"], 100.0)
        self.assertEqual(health["sub_scores"]["uniqueness"], 100.0)
        self.assertEqual(health["sub_scores"]["outlier_control"], 100.0)
        self.assertEqual(health["sub_scores"]["type_consistency"], 100.0)

    def test_data_health_score_degraded_dataset(self):
        """Verify score properly docks points for nulls, duplicates, outliers, and zero-variance."""
        mock_df = MagicMock()
        mock_df.height = 100
        mock_df.width = 2
        mock_df.columns = ["feat_a", "feat_b"]

        def mock_col(name):
            col = MagicMock()
            col.null_count.return_value = 20 if name == "feat_a" else 0
            return col

        mock_df.get_column.side_effect = mock_col

        numeric = ["feat_a", "feat_b"]
        numeric_summary = {
            "feat_a": {"count": 80, "outlier_count_iqr": 15, "std": 0.0, "min": 5.0, "max": 5.0}, # zero variance
            "feat_b": {"count": 100, "outlier_count_iqr": 10, "std": 3.0, "min": 1.0, "max": 10.0},
        }

        health = _calculate_data_health_score(mock_df, numeric, [], numeric_summary, {}, 10)
        self.assertLess(health["score"], 90.0)
        self.assertIn("feat_a", health["zero_variance_columns"])
        self.assertLess(health["sub_scores"]["completeness"], 100.0)
        self.assertLess(health["sub_scores"]["uniqueness"], 100.0)

    def test_data_health_empty_dataset(self):
        """Verify empty datasets handle boundary zero-division safely."""
        mock_df = MagicMock()
        mock_df.height = 0
        mock_df.width = 0
        mock_df.columns = []

        health = _calculate_data_health_score(mock_df, [], [], {}, {}, 0)
        self.assertEqual(health["score"], 0.0)
        self.assertEqual(health["grade"], "Critical")

    def test_missingness_alerts_severity_tiers(self):
        """Verify proper severity classification across critical, high, medium, and low tiers."""
        mock_df = MagicMock()
        mock_df.height = 100
        mock_df.columns = ["col_crit", "col_high", "col_med", "col_low", "col_clean"]

        def mock_col(name):
            col = MagicMock()
            rates = {"col_crit": 60, "col_high": 25, "col_med": 10, "col_low": 2, "col_clean": 0}
            col.null_count.return_value = rates[name]
            return col

        mock_df.get_column.side_effect = mock_col

        alerts = _missingness_alerts(mock_df)
        self.assertEqual(len(alerts), 4) # col_clean is omitted
        severities = {a["column"]: a["severity"] for a in alerts}
        self.assertEqual(severities["col_crit"], "critical")
        self.assertEqual(severities["col_high"], "high")
        self.assertEqual(severities["col_med"], "medium")
        self.assertEqual(severities["col_low"], "low")

    def test_ml_readiness_multicollinearity_and_zero_variance(self):
        """Verify detection of collinear pairs (|r| > 0.85) and zero variance."""
        correlations = {
            "feature_x": {"feature_x": 1.0, "feature_y": 0.94, "feature_z": 0.12},
            "feature_y": {"feature_x": 0.94, "feature_y": 1.0, "feature_z": 0.05},
            "feature_z": {"feature_x": 0.12, "feature_y": 0.05, "feature_z": 1.0},
        }
        numeric_summary = {
            "feature_x": {"std": 10.0, "min": 1.0, "max": 50.0, "count": 100},
            "feature_y": {"std": 12.0, "min": 2.0, "max": 60.0, "count": 100},
            "feature_z": {"std": 0.0, "min": 5.0, "max": 5.0, "count": 100}, # zero var
        }
        mock_df = MagicMock()
        mock_df.height = 100

        readiness = _ml_readiness_warnings(
            mock_df,
            ["feature_x", "feature_y", "feature_z"],
            [],
            correlations,
            numeric_summary,
            {},
        )
        self.assertEqual(readiness["status"], "warnings_detected")
        self.assertEqual(len(readiness["multicollinearity_flags"]), 1)
        self.assertEqual(readiness["multicollinearity_flags"][0]["pearson_r"], 0.94)
        self.assertEqual(len(readiness["zero_variance_columns"]), 1)
        self.assertEqual(readiness["zero_variance_columns"][0]["column"], "feature_z")

    def test_pydantic_contracts_validation(self):
        """Verify that Pydantic contracts in app.agent.contracts validate properly."""
        from app.agent.contracts import (
            BusinessInsights,
            DataHealthScore,
            DataHealthSubScores,
            MissingnessAlert,
            MLReadinessWarnings,
            ParetoAnalysisResult,
        )

        sub_scores = DataHealthSubScores(
            completeness=95.0,
            uniqueness=100.0,
            outlier_control=90.0,
            type_consistency=100.0,
        )
        health = DataHealthScore(
            score=96.2,
            grade="Excellent",
            rating_description="Production ready",
            sub_scores=sub_scores,
            total_cells=400,
            total_nulls=5,
            duplicate_rows=0,
            total_outliers=2,
            zero_variance_columns=[],
        )
        self.assertEqual(health.score, 96.2)
        self.assertEqual(health.grade, "Excellent")

        pareto = ParetoAnalysisResult(
            applicable=True,
            column="revenue",
            is_pareto=True,
            top_20_pct_volume_share=75.0,
            pct_records_generating_80_pct=25.0,
            records_generating_80_pct=25,
            total_records_evaluated=100,
            total_volume=10000.0,
            summary="Top 20% records generate 75% volume.",
        )
        self.assertTrue(pareto.is_pareto)

        alert = MissingnessAlert(
            column="age",
            missing_count=10,
            missing_pct=10.0,
            severity="medium",
            recommended_strategy="Median imputation",
        )
        self.assertEqual(alert.severity, "medium")

        ml_warn = MLReadinessWarnings(
            status="ready",
            multicollinearity_flags=[],
            zero_variance_columns=[],
            high_cardinality_columns=[],
            candidate_targets=[],
        )
        self.assertEqual(ml_warn.status, "ready")

        insights = BusinessInsights(
            pareto_analysis=pareto,
            missingness_alerts=[alert],
            ml_readiness=ml_warn,
        )
        self.assertEqual(len(insights.missingness_alerts), 1)

    def test_pareto_analysis_edge_cases(self):
        """Verify Pareto handles insufficient records or missing volume candidates safely."""
        mock_df = MagicMock()
        mock_df.height = 3
        result = _pareto_analysis(mock_df, ["revenue"])
        self.assertFalse(result["applicable"])
        self.assertIn("Insufficient records", result["reason"])

        mock_df.height = 10
        result_no_num = _pareto_analysis(mock_df, [])
        self.assertFalse(result_no_num["applicable"])

    def test_grounding_metric_contract_invariants(self):
        """Verify that health scores, Pareto, and ML readiness pass decision safety grounding."""
        from app.agent.grounding import validate_metric_contract

        metrics = {
            "exploratory_data_analysis": {
                "non_graphical": {
                    "data_health_score": 95.0,
                    "business_insights": {
                        "pareto_analysis": {
                            "applicable": True,
                            "top_20_pct_volume_share": 80.0,
                            "pct_records_generating_80_pct": 20.0,
                        },
                        "missingness_alerts": [
                            {"column": "feat", "missing_pct": 12.5, "severity": "medium"}
                        ],
                        "ml_readiness": {
                            "multicollinearity_flags": [
                                {"feature_1": "a", "feature_2": "b", "pearson_r": 0.88}
                            ]
                        },
                    },
                }
            }
        }
        errors = validate_metric_contract(metrics)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
