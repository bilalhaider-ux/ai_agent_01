# DataSnap

DataSnap turns an uploaded tabular dataset into a verified, comprehensive exploratory data analysis (EDA) report. It runs a deterministic multi-phase workflow covering data health, univariate profiles, bivariate relationships, multivariate relationships, statistical tests, visualizations, and evidence-backed next actions.

## Product Flow

1. Open the DataSnap landing page.
2. Start an analysis and upload a CSV, XLSX, Parquet, TSV, JSON, or JSONL dataset.
3. Optionally describe the analysis focus.
4. DataSnap runs the deterministic EDA workflow on the uploaded file.
5. Review the completed EDA report at its dedicated report route.
6. Save the report explicitly to the browser's local report library, or download Markdown/HTML.

Saved reports are local to the current browser. No user account or application database is required for this release.

## What Is Included

- Phase 1 data health: exact shape, data types, missing-value percentages, duplicates, IQR outliers, and high-cardinality categorical columns.
- Phase 2 statistical discovery: variance, skewness, kurtosis, Pearson/Spearman correlations, ANOVA or Welch t-tests, and Chi-square tests where valid.
- Univariate, bivariate, and multivariate profiles with JSON-serializable metrics.
- Polars, SciPy, and Matplotlib analysis with bounded chart sampling for large datasets.
- EDA reports with verified metrics, visualizations, statistical test outputs, provenance, limitations, and evidence-backed next actions.
- Professional HTML and Markdown report rendering.
- Browser report archive using IndexedDB with a localStorage fallback.
- Redis-backed anonymous quota: five analysis requests per rolling hour using IP and browser-token counters.
- Dark-first Vite/React frontend with landing, analysis, saved reports, and full report views.

## Repository Structure

```text
backend/
  app/
    agent/       LangGraph workflow, provider factory, contracts, and execution
    api/         FastAPI routes
    services/    uploads, analysis, reports, and Redis quota
  tests/         unittest coverage
frontend/
  src/           Vite/React application and browser report storage
Procfile         Heroku web process
requirements.txt Backend Python dependencies
```

## Local Development

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp backend/.env.example backend/.env
```

Set the provider and credentials in `backend/.env`. Keep the file local and never commit it.

Start the API from the repository root:

```bash
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`. Set `VITE_AGENT_API_URL` in `frontend/.env` only when the API is not running at `http://127.0.0.1:8000`.

## Configuration

Backend values belong in `backend/.env` locally or Heroku Config Vars in production:

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER` | Retained for provider compatibility; the active EDA workflow is deterministic. |
| `GEMINI_API_KEY` | Backend-only Gemini credential. |
| `GEMINI_MODEL` | Primary model, normally `gemini-3.1-flash-lite`. |
| `GEMINI_FALLBACK_MODELS` | Comma-separated fallback models. |
| `UPSTASH_REDIS_REST_URL` | Upstash REST endpoint for quota storage. |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash REST token. |
| `RATE_LIMIT_SECRET` | Long random signing secret for quota identity keys. |
| `MAX_REQUESTS_PER_HOUR` | Anonymous analysis limit, normally `5`. |
| `COOKIE_SECURE` | `false` locally; `true` behind HTTPS. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins. |
| `MAX_RETRY_COUNT` | Compatibility retry budget for the retained workflow contract. |
| `EXECUTION_TIMEOUT_SECONDS` | Compatibility execution timeout setting. |
| `MAX_UPLOAD_SIZE_BYTES` | Upload limit in bytes. |

The frontend only receives `VITE_AGENT_API_URL`. Provider keys, Redis tokens, and signing secrets must never be placed in frontend environment variables.

## API

Health check:

```text
GET /health
```

Create an analysis with multipart form data:

```text
POST /api/v1/analyze
```

Required fields:

- `query`: optional analysis focus
- `dataset`: uploaded file

The response includes an `analysis_id`, status, phase-derived verified metrics, charts, report content, and grounding metadata. Provider/model fields remain in the compatibility contract but are not required for deterministic EDA calculations.

Report endpoints:

```text
GET /api/v1/reports/{analysis_id}
GET /api/v1/reports/{analysis_id}/markdown
GET /api/v1/reports/{analysis_id}/html
```

Quota headers are returned on analysis responses:

```text
X-RateLimit-Limit
X-RateLimit-Remaining
X-RateLimit-Reset
```

## Testing

Run the complete backend suite:

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

Build the frontend:

```bash
cd frontend
npm run build
```

Use `LLM_PROVIDER=mock` for offline backend tests. For a real local smoke test, start both services, open the frontend, upload `backend/data/sample_sales_data.csv`, and run EDA. A successful result opens a dedicated `/report/{analysis_id}` view. Saving is explicit; completed reports are not automatically added to the local library.

## Deployment Summary

The backend is configured for Heroku through the root `Procfile`. The frontend is a standalone Vite app for Vercel. Follow [Guide.md](Guide.md) for the complete release procedure and environment mapping.

## Important Limitations

- Browser-saved reports disappear when the user clears site data or changes device/browser.
- The backend report store is process memory only and is not a durable server archive.
- Statistical significance and correlation do not establish causation. Reports remain pending human review.
- The frontend currently provides HTML and Markdown downloads; an XLSX export requires a separate backend export endpoint.

## License

MIT. See [LICENSE](LICENSE).
