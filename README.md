# AI Agent 01

AI Agent 01 turns a business question and a tabular dataset into a decision-ready analytics report. It profiles the data, plans an analysis, generates Polars/SciPy/Matplotlib code, executes that code in an isolated timed subprocess, self-corrects runtime failures, and returns findings, metrics, charts, Markdown, and HTML.

## What It Does

The product is designed for analysts, operators, and decision-makers who need a fast first-pass exploration of sales and other structured datasets. A typical flow is:

1. Upload a dataset and describe the business question.
2. Review the profiled schema, data-quality checks, analytical plan, and execution result.
3. Use the machine-verified metrics and visualizations to guide human-reviewed decisions.
4. Download or display the complete Markdown or HTML report.

The response marks narrative text as advisory. Downstream calculations must use `grounding.authoritative_metrics`.

## Current Capabilities

- Dataset profiling: schema, data types, row/column counts, nulls, duplicates, sample, and summary statistics.
- LangGraph workflow: planning, code generation, isolated execution, retry/self-correction, and synthesis.
- LLM providers: Gemini, Mistral, legacy OpenAI/Ollama compatibility, and deterministic Mock testing.
- Supported uploads: CSV, XLSX, Parquet, TSV, JSON, and JSONL.
- Decision reports: executive summary, direct answer, statistical insights, recommendations, metrics, and embedded charts.
- Safety metadata: metric validation, dataset hash, provenance, data quality, reproducibility hash, assumption status, drift status, and human-review status.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp backend/.env.example backend/.env
```

Add one backend provider key to `backend/.env`. Never put a real key in GitHub, frontend code, Postman collections, or issue reports.

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-3.8-flash
```

Start the API from the repository root:

```bash
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For offline testing use `LLM_PROVIDER=mock` and do not provide an external API key.

## API

Health check:

```text
GET /health
```

Analysis request:

```text
POST /api/v1/analyze
```

Send multipart form data with required `query` text and `dataset` file. Optional `provider` and `model` fields override the backend defaults for that request.

Reports:

```text
GET /api/v1/reports/{analysis_id}
GET /api/v1/reports/{analysis_id}/markdown
GET /api/v1/reports/{analysis_id}/html
```

The current report store is process memory only. Reports are not durable across restarts or Heroku dyno changes.

## Configuration

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER` | `gemini`, `mistral`, `mock`, `openai`, or `ollama` |
| `GEMINI_API_KEY` | Gemini backend key; required for Gemini |
| `GEMINI_MODEL` | Gemini model identifier |
| `MISTRAL_API_KEY` | Mistral backend key; required for Mistral |
| `MISTRAL_MODEL` | Mistral model identifier |
| `MAX_RETRY_COUNT` | Generated-code self-correction budget |
| `EXECUTION_TIMEOUT_SECONDS` | Child-process execution limit |
| `MAX_UPLOAD_SIZE_BYTES` | Upload size limit; default 50 MiB |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed browser origins |

## Testing

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

The automated suite uses Mock and does not require network access or API keys.

## Heroku Deployment

The root [Procfile](Procfile) runs Gunicorn with Uvicorn workers. Connect the GitHub repository and deploy the intended branch. Set these as Heroku Config Vars, not files:

```text
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.8-flash
MAX_RETRY_COUNT=3
EXECUTION_TIMEOUT_SECONDS=45
CORS_ALLOWED_ORIGINS=https://your-frontend.example
```

After deployment, verify `/health` before sending an analysis request. Heroku's filesystem is ephemeral and the current in-memory report store is not a permanent archive. No automatic deployment or permanent storage is claimed by this repository.

## Decision-Grade EDA Protocol

The system labels results `verified_metrics_only`. It records data quality, metric keys, dataset SHA-256, provider/model, generated-code hash, and a `pending_human_review` decision status. It does not treat correlation as causation, missing data as zero, or LLM narrative as an authoritative metric source. Confidence intervals and drift baselines are reported as unavailable unless explicitly computed.

## Security

See [SECURITY.md](SECURITY.md). Generated code runs in a separate timed subprocess, but this is not a hardened container boundary for hostile multi-tenant workloads. Use stronger isolation before exposing arbitrary uploads to untrusted users.

## License

MIT. See [LICENSE](LICENSE).
