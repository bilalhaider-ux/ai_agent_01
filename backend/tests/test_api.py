import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
    from app.main import app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from app.agent.llm import get_llm
try:
    from app.agent.minifier import minify_dataset
except ImportError:
    minify_dataset = None


class TestLlmConfig(unittest.TestCase):
    def test_mistral_requires_key(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": ""}, clear=False):
            with self.assertRaisesRegex(ValueError, "MISTRAL_API_KEY"):
                get_llm(provider="mistral")

    def test_gemini_requires_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False):
            with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY"):
                get_llm(provider="gemini")


@unittest.skipUnless(HAS_FASTAPI, "fastapi not installed")
class TestApi(unittest.TestCase):
    def test_health_and_missing_report(self):
        client = TestClient(app)
        self.assertEqual(client.get("/health").status_code, 200)
        self.assertEqual(client.get("/api/v1/reports/missing").status_code, 404)

    def test_mock_analysis_api_returns_reports(self):
        client = TestClient(app)
        dataset = Path(__file__).parent.parent / "data" / "sample_sales_data.csv"
        with dataset.open("rb") as handle:
            response = client.post(
                "/api/v1/analyze",
                data={"query": "Analyze revenue and returns", "provider": "mock"},
                files={"dataset": ("sample_sales_data.csv", handle, "text/csv")},
            )
        self.assertEqual(response.status_code, 202, response.text)
        queued = response.json()
        self.assertIn(queued["status"], {"queued", "running"})
        result = client.get(f"/api/v1/analyses/{queued['analysis_id']}").json()
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["charts"])
        self.assertEqual(result["grounding"]["status"], "eda_only")
        self.assertEqual(
            result["grounding"]["summary_type"],
            "professional_non_graphical_and_visual_exploratory_data_analysis",
        )
        self.assertGreater(result["grounding"]["data_quality"]["row_count"], 0)
        self.assertGreater(result["grounding"]["metric_count"], 0)
        eda = result["metrics"]["exploratory_data_analysis"]
        self.assertIn("correlation_matrix_pearson", eda)
        self.assertIn("quality_flags", eda)
        self.assertIn("univariate", eda)
        self.assertIn("bivariate", eda)
        self.assertIn("multivariate", eda)
        self.assertIn("missing_percentages", eda)
        self.assertIn("high_cardinality_categorical_columns", eda)
        self.assertIn("statistical_tests", eda)
        self.assertIn("categorical_numeric_tests", eda["statistical_tests"])
        self.assertIn("categorical_categorical_tests", eda["statistical_tests"])
        self.assertTrue(eda["bivariate"]["numeric_pairs"])
        self.assertTrue(eda["multivariate"]["strongest_numeric_relationships"])
        self.assertTrue(any("Box plot" in item for item in result["grounding"].get("visualization_types", [])) or result["charts"])
        self.assertEqual(result["generated_code"], "")
        self.assertIn("# Exploratory Data Analysis Report", result["markdown_report"])
        self.assertIn("## Non-Graphical Statistical Summaries", result["markdown_report"])
        self.assertIn("## Data Visualizations", result["markdown_report"])
        self.assertIn("## Suggestion by DataSnap", result["markdown_report"])
        self.assertIn("Suggestion by DataSnap", result["html_report"])
        self.assertIn("<img", result["html_report"])
        analysis_id = result["analysis_id"]
        self.assertEqual(client.get(f"/api/v1/reports/{analysis_id}/markdown").status_code, 200)
        self.assertEqual(client.get(f"/api/v1/reports/{analysis_id}/html").status_code, 200)

    def test_supported_text_formats_and_rejected_extension(self):
        with TemporaryDirectory() as directory:
            directory_path = Path(directory)
            tsv_path = directory_path / "dataset.tsv"
            tsv_path.write_text("category\trevenue\nA\t10\n", encoding="utf-8")
            jsonl_path = directory_path / "dataset.jsonl"
            jsonl_path.write_text('{"category":"A","revenue":10}\n', encoding="utf-8")
            self.assertEqual(minify_dataset(tsv_path).row_count, 1)
            self.assertEqual(minify_dataset(jsonl_path).row_count, 1)

        response = TestClient(app).post(
            "/api/v1/analyze",
            data={"query": "analyze", "provider": "mock"},
            files={"dataset": ("dataset.exe", b"not a dataset", "application/octet-stream")},
        )
        self.assertEqual(response.status_code, 400)

    def test_provider_rate_limit_has_clear_response(self):
        with patch("app.api.routes_analysis.process_analysis"):
            response = TestClient(app).post(
                "/api/v1/analyze",
                data={"query": "analyze", "provider": "mistral"},
                files={"dataset": ("sample.csv", b"a,b\n1,2\n", "text/csv")},
            )
        self.assertEqual(response.status_code, 202)
        job_id = response.json()["analysis_id"]
        self.assertEqual(TestClient(app).get(f"/api/v1/analyses/{job_id}").status_code, 200)


if __name__ == "__main__":
    unittest.main()
