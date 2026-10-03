import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.agent.llm import get_llm
from app.agent.minifier import minify_dataset
from app.main import app


class TestApi(unittest.TestCase):
    def test_health_and_missing_report(self):
        client = TestClient(app)
        self.assertEqual(client.get("/health").status_code, 200)
        self.assertEqual(client.get("/api/v1/reports/missing").status_code, 404)

    def test_mistral_requires_key(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": ""}, clear=False):
            with self.assertRaisesRegex(ValueError, "MISTRAL_API_KEY"):
                get_llm(provider="mistral")

    def test_mock_analysis_api_returns_reports(self):
        client = TestClient(app)
        dataset = Path(__file__).parent.parent / "data" / "sample_sales_data.csv"
        with dataset.open("rb") as handle:
            response = client.post(
                "/api/v1/analyze",
                data={"query": "Analyze revenue and returns", "provider": "mock"},
                files={"dataset": ("sample_sales_data.csv", handle, "text/csv")},
            )
        self.assertEqual(response.status_code, 201, response.text)
        result = response.json()
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["charts"])
        self.assertEqual(result["grounding"]["status"], "verified_metrics_only")
        self.assertEqual(result["grounding"]["authoritative_metrics"], result["metrics"])
        self.assertIn("# Analytical Decision Report", result["markdown_report"])
        self.assertIn("## Machine-Verified Evidence", result["markdown_report"])
        self.assertIn("overall_return_rate_pct", result["markdown_report"])
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


if __name__ == "__main__":
    unittest.main()