# DataSnap Deployment

[View the Tech Stack](#tech-stack) · [Deployment Steps](#deployment-steps)

Deploy DataSnap directly from the GitHub repository using the Heroku and Vercel dashboards. You do not need to clone the project or use the terminal.

## Tech Stack

### Frontend

- **React** and **Vite** for the web application.
- **Lucide React** for interface icons.
- **IndexedDB** with a `localStorage` fallback for saved reports in the browser.
- **Vercel** for frontend hosting.

### Backend and API

- **Python** with **FastAPI** for the backend API.
- **Uvicorn** for local development.
- **Gunicorn with Uvicorn workers** for the Heroku web process.
- **Pydantic** for data validation and API contracts.
- **python-multipart** for dataset uploads.

### EDA and data analysis

- **LangGraph** for workflow compatibility and stage orchestration.
- **Polars** for tabular data processing.
- **Pandas, PyArrow, and Fastexcel** for data loading and file support.
- **SciPy** for statistical analysis.
- **Matplotlib** for charts.
- Deterministic Phase 1, Phase 2, and Phase 3 EDA reporting.

### Storage, security, and deployment

- **Upstash Redis** for optional shared rate-limit storage.
- Anonymous request limits using IP and browser-token counters.
- **Heroku** for the backend.
- **GitHub** as the source repository and deployment connection.

## Deployment Steps

### What you need

- Access to this project's GitHub repository
- [Heroku account](https://dashboard.heroku.com/)
- [Vercel account](https://vercel.com/) connected to GitHub
DataSnap has two parts:

- **Backend:** Heroku
- **Frontend:** Vercel

### 1. Deploy the backend to Heroku

1. Open the Heroku Dashboard and click **New → Create new app**.
2. Enter a unique app name and click **Create app**.
3. Open the app's **Deploy** tab.
4. Select **Deployment method: GitHub**.
5. Connect GitHub and search for the `ai_agent_01` repository.
6. Select the `main` branch and click **Deploy Branch**.

Use the repository root. Do not set `backend` as the root directory.

### Add Heroku environment variables

In your Heroku app, open **Settings → Config Vars → Reveal Config Vars**. Add each key and value, then click **Add**:

| Key | Value |
| --- | --- |
| `LLM_PROVIDER` | `mock` or the configured compatibility provider |
| `GEMINI_API_KEY` | Only required if an external compatibility provider is enabled |
| `GEMINI_MODEL` | Compatibility setting; not required for deterministic EDA |
| `GEMINI_FALLBACK_MODELS` | Compatibility setting; not required for deterministic EDA |
| `COOKIE_SECURE` | `true` |
| `RATE_LIMIT_SECRET` | Any long, private random value |
| `MAX_REQUESTS_PER_HOUR` | `5` |
| `MAX_RETRY_COUNT` | `3` |
| `EXECUTION_TIMEOUT_SECONDS` | `45` |
| `MAX_UPLOAD_SIZE_BYTES` | `52428800` |
| `CORS_ALLOWED_ORIGINS` | Temporarily use `https://your-project.vercel.app` |

Do not share `GEMINI_API_KEY` or `RATE_LIMIT_SECRET`. After deployment, copy your Heroku backend URL. For example:

```text
https://your-app-name.herokuapp.com
```

Check the backend by opening this URL in your browser:

```text
https://your-app-name.herokuapp.com/health
```

If you see `{"status":"ok"}`, the backend is working.

### 2. Deploy the frontend to Vercel

1. Open Vercel and click **Add New → Project**.
2. Import the same GitHub repository.
3. Set **Root Directory** to `frontend`.
4. Keep the framework set to **Vite**.
5. In **Environment Variables**, add:

   | Key | Value |
   | --- | --- |
   | `VITE_AGENT_API_URL` | Your Heroku backend URL |

   Use only the base Heroku URL. Do not add `/api/v1/analyze` or a trailing slash.

6. Click **Deploy**.

After deployment, copy your Vercel frontend URL. For example:

```text
https://your-project.vercel.app
```

### 3. Connect Heroku and Vercel

Return to Heroku and open **Settings → Config Vars**. Edit `CORS_ALLOWED_ORIGINS` and paste your exact Vercel URL:

```text
https://your-project.vercel.app
```

Do not add a trailing slash or a page path. Save the value and restart the Heroku app if needed.

### 4. Test the app

Open your Vercel URL and:

1. Click **Run EDA**.
2. Upload a dataset.
3. Optionally enter an analysis focus.
4. Review the phased EDA report.

If the report opens, the deployment is complete.

### Security note

Never commit `.env` files, API keys, Redis tokens, or passwords to GitHub. Add provider keys only when a compatibility provider is enabled. Add only `VITE_AGENT_API_URL` to Vercel.
