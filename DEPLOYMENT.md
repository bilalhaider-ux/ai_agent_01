# DataSnap Deployment Guide

This guide deploys DataSnap as two services:

- **Backend:** FastAPI on Heroku
- **Frontend:** Vite/React on Vercel

The frontend sends requests to the backend URL through `VITE_AGENT_API_URL`. The backend must allow the deployed frontend URL through `CORS_ALLOWED_ORIGINS`.

## 1. Prerequisites

Install or create accounts for:

- Git and GitHub access to this repository
- Heroku CLI and a Heroku account
- Vercel account connected to GitHub
- Google AI Studio access for a Gemini API key
- Upstash Redis, optional but recommended for shared production rate limiting

Never commit API keys, Redis tokens, or local `.env` files. Keep provider credentials in Heroku Config Vars only.

## 2. Get the source

Clone the repository and enter it:

```bash
git clone https://github.com/bilalhaider-ux/ai_agent_01.git
cd ai_agent_01
```

The Heroku `Procfile` is at the repository root. The Vercel project must use `frontend` as its Root Directory.

## 3. Create the Gemini API key

1. Open [Google AI Studio](https://aistudio.google.com/).
2. Create or select a Google project.
3. Create an API key under **Get API key**.
4. Store the key as the Heroku Config Var `GEMINI_API_KEY`.

Do not put `GEMINI_API_KEY` in Vercel or in any `VITE_*` variable. Vite variables are exposed to the browser.

## 4. Create the Heroku backend

Log in and create a new Heroku app. Choose a unique app name:

```bash
heroku login
heroku create <your-backend-app-name>
```

The resulting URL will look like:

```text
https://<your-backend-app-name>.herokuapp.com
```

The repository already contains the Python dependencies and root `Procfile`. Deploy from the repository root:

```bash
git push heroku main
```

If the current branch is not `main`, push it explicitly:

```bash
git push heroku <branch-name>:main
```

## 5. Configure Heroku Config Vars

Set the required production values. Replace every placeholder before running the command:

```bash
heroku config:set \
  LLM_PROVIDER=gemini \
  GEMINI_API_KEY="<key-from-google-ai-studio>" \
  GEMINI_MODEL=gemini-3.1-flash-lite \
  GEMINI_FALLBACK_MODELS=gemini-3.5-flash-lite,gemini-2.5-flash-lite \
  CORS_ALLOWED_ORIGINS="https://<your-vercel-domain>" \
  COOKIE_SECURE=true \
  MAX_RETRY_COUNT=3 \
  EXECUTION_TIMEOUT_SECONDS=45 \
  MAX_UPLOAD_SIZE_BYTES=52428800 \
  MAX_REQUESTS_PER_HOUR=5 \
  RATE_LIMIT_SECRET="<long-random-secret>" \
  --app <your-backend-app-name>
```

Generate a signing secret locally instead of inventing a short value:

```bash
openssl rand -hex 32
```

### Optional Upstash Redis variables

The application uses an in-memory limiter when Redis variables are absent. For shared, restart-resistant production quotas, create a database at [Upstash](https://upstash.com/) and copy its REST credentials:

```bash
heroku config:set \
  UPSTASH_REDIS_REST_URL="<upstash-rest-url>" \
  UPSTASH_REDIS_REST_TOKEN="<upstash-rest-token>" \
  --app <your-backend-app-name>
```

### Config Var reference

| Variable | Source or value | Required | Purpose |
| --- | --- | --- | --- |
| `LLM_PROVIDER` | `gemini` | Yes | Selects the production provider |
| `GEMINI_API_KEY` | Google AI Studio | Yes | Backend-only Gemini credential |
| `GEMINI_MODEL` | Usually `gemini-3.1-flash-lite` | Yes | Primary Gemini model |
| `GEMINI_FALLBACK_MODELS` | Comma-separated Gemini model names | No | Fallback models for retryable failures |
| `CORS_ALLOWED_ORIGINS` | Exact Vercel origin, no trailing slash | Yes | Allows browser requests from the frontend |
| `COOKIE_SECURE` | `true` in HTTPS production | Yes | Enables secure quota cookies |
| `RATE_LIMIT_SECRET` | Random value from `openssl` | Yes | Signs anonymous quota identity keys |
| `MAX_REQUESTS_PER_HOUR` | `5` or an intentional limit | No | Anonymous analysis quota |
| `MAX_RETRY_COUNT` | `3` | No | Agent code-repair attempts |
| `EXECUTION_TIMEOUT_SECONDS` | `45` | No | Generated analysis subprocess limit |
| `MAX_UPLOAD_SIZE_BYTES` | `52428800` | No | 50 MB upload limit |
| `UPSTASH_REDIS_REST_URL` | Upstash REST URL | No | Shared quota storage |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash REST token | No | Upstash authentication |

After changing Config Vars, restart the app if Heroku does not restart it automatically:

```bash
heroku restart --app <your-backend-app-name>
```

## 6. Verify the backend

Check the health endpoint:

```bash
curl -i https://<your-backend-app-name>.herokuapp.com/health
```

Expected response:

```json
{"status":"ok"}
```

Check the CORS preflight after the Vercel URL is known:

```bash
curl -i -X OPTIONS \
  https://<your-backend-app-name>.herokuapp.com/api/v1/analyze \
  -H "Origin: https://<your-vercel-domain>" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"
```

The response must include:

```text
access-control-allow-origin: https://<your-vercel-domain>
```

## 7. Deploy the frontend to Vercel

1. Open Vercel and choose **Add New Project**.
2. Import `bilalhaider-ux/ai_agent_01` from GitHub.
3. Set **Root Directory** to `frontend`.
4. Keep the framework as Vite or let Vercel detect it.
5. Set the production environment variable:

   ```text
   VITE_AGENT_API_URL=https://<your-backend-app-name>.herokuapp.com
   ```

6. Deploy the project.

The frontend contains `frontend/vercel.json`, which serves the React app for direct URLs such as `/analyze`, `/reports`, and `/report/<id>`.

Copy the final Vercel production URL, then update the Heroku variable with the exact origin:

```bash
heroku config:set \
  CORS_ALLOWED_ORIGINS="https://<your-vercel-domain>" \
  --app <your-backend-app-name>
```

Do not add a trailing slash and do not include a path such as `/analyze`.

## 8. End-to-end test

1. Open the Vercel production URL.
2. Go to `/analyze` directly in the address bar.
3. Upload `backend/data/sample_sales_data.csv`.
4. Enter a business question.
5. Run the analysis.
6. Confirm that the report opens at `/report/<analysis-id>`.
7. Save the report and verify it appears under `/reports`.

For a backend-only smoke test, use the mock provider. This avoids Gemini usage and confirms the upload and analysis pipeline:

```bash
curl -X POST https://<your-backend-app-name>.herokuapp.com/api/v1/analyze \
  -F "query=Analyze revenue" \
  -F "provider=mock" \
  -F "dataset=@backend/data/sample_sales_data.csv"
```

## 9. Troubleshooting

### `CORS policy` or missing `Access-Control-Allow-Origin`

- Confirm `CORS_ALLOWED_ORIGINS` exactly matches the Vercel origin.
- Use `https://`, not `http://`.
- Remove a trailing slash.
- Restart Heroku after changing the Config Var.
- Check the browser request's `Origin` value; custom domains need their own entry.

### `429 Too Many Requests`

The default anonymous limit is five analyses per rolling hour. Wait for the reset time in `X-RateLimit-Reset`, or intentionally increase `MAX_REQUESTS_PER_HOUR`. Repeated failed tests can consume quota.

### `503`, `H13`, or `WORKER TIMEOUT`

Inspect Heroku logs:

```bash
heroku logs --tail --app <your-backend-app-name>
```

Gemini analysis is synchronous and can be slow. Gunicorn is configured with a longer worker timeout, but Heroku's router still has a short request limit. A durable solution for analyses that exceed that limit is a background job plus a status-polling endpoint.

### Vercel direct URL returns `404`

Confirm the Vercel Root Directory is `frontend` and that `frontend/vercel.json` is included in the deployed commit. Redeploy after changing the Root Directory.

## 10. Security checklist

- Never commit `.env`, API keys, Redis tokens, or signing secrets.
- Keep provider credentials in Heroku Config Vars only.
- Keep `VITE_AGENT_API_URL` as the only backend-related frontend variable.
- Use `COOKIE_SECURE=true` in production.
- Keep CORS restricted to known frontend origins.
- Rotate any credential that was accidentally exposed.