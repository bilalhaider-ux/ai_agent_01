# AI Agent 01

AI Agent 01 is a LangGraph-powered data analytics service. It profiles an uploaded dataset, asks an LLM to plan and generate Polars/SciPy/Matplotlib analysis code, executes that code in a timed child process, retries failures, and returns a decision-ready report with metrics and embedded charts.

## Architecture

The FastAPI application lives in `backend/app`. `app/agent` contains the existing six-stage workflow: context minification, intent and plan, code generation, isolated execution, self-correction, and output synthesis. `app/services` handles uploads, pipeline invocation, and report formatting. The frontend directory is intentionally empty until a client is added.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp backend/.env.example .env
export PYTHONPATH=backend
uvicorn app.main:app --reload --app-dir backend
```

Use `LLM_PROVIDER=mock` for an offline run and automated tests. Production uses Mistral:

```bash
export LLM_PROVIDER=mistral
export MISTRAL_API_KEY=your-key
export MISTRAL_MODEL=mistral-small-latest
```

## API

- `GET /health` checks service availability.
- `POST /api/v1/analyze` accepts multipart `query`, `dataset`, and optional `provider`/`model` fields.
- `GET /api/v1/reports/{analysis_id}` returns the complete structured result.
- `GET /api/v1/reports/{analysis_id}/markdown` returns the Markdown report.
- `GET /api/v1/reports/{analysis_id}/html` returns the HTML report.

Supported uploads are CSV, XLSX, Parquet, TSV, JSON, and JSONL. Uploads are limited by `MAX_UPLOAD_SIZE_BYTES` (50 MiB by default), stored temporarily, and removed after analysis. Filenames are validated and API keys are never sent to a frontend.

## Configuration

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER` | `mistral` for production or `mock` for tests |
| `MISTRAL_API_KEY` | Required for Mistral; never commit it |
| `MISTRAL_MODEL` | Defaults to `mistral-small-latest` |
| `MAX_RETRY_COUNT` | Code self-correction budget |
| `EXECUTION_TIMEOUT_SECONDS` | Child-process execution limit |
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser origins |
| `MAX_UPLOAD_SIZE_BYTES` | Maximum dataset size |

## Testing

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

The tests use Mock and do not require Mistral access. A local mock analysis can be run through the API with the sample file at `backend/data/sample_sales_data.csv`.

## Heroku

The root `Procfile` runs Gunicorn with Uvicorn workers. Set `MISTRAL_API_KEY`, `MISTRAL_MODEL`, `LLM_PROVIDER`, `MAX_RETRY_COUNT`, `EXECUTION_TIMEOUT_SECONDS`, and `CORS_ALLOWED_ORIGINS` as Heroku Config Vars. Heroku's local filesystem is ephemeral: reports are held in process memory and are not durable across restarts or dyno changes. No automatic deployment is configured.

## Limitations and Security

Generated code runs in a separate subprocess with a timeout and temporary working directory. This is a constrained execution boundary, not a hardened container or arbitrary-code security guarantee; production deployments should add stronger isolation for untrusted multi-tenant workloads. Report retention is not persistent, and the current API performs analysis synchronously.

## Decision-Grade EDA Protocol

The API marks results as `verified_metrics_only`. Downstream calculations must use `grounding.authoritative_metrics`, never numbers copied from the LLM narrative. The report includes a Machine-Verified Evidence section generated from the successful isolated execution result.

1. **Data contract:** record file type, schema, row count, null counts, and profiling errors before analysis.
2. **Metric provenance:** every decision metric must have a stable key and be copied from execution output.
3. **No evidence, no claim:** missing values remain unknown; the agent must not fill them with zero or estimates.
4. **Statistical discipline:** correlation is not causation; significance claims require an observed test statistic and p-value.
5. **Reproducibility:** retain the query, provider/model, plan, generated code, retry trace, metrics, and chart artifacts with an analysis id in a durable store before production use.
6. **Decision gate:** recommendations are advisory until a human reviews the evidence, assumptions, sample size, data quality, and business impact.
7. **Drift monitoring:** compare schema, row counts, null rates, metric distributions, and model output across runs before accepting automated decisions.

## License

MIT. See [LICENSE](LICENSE).
