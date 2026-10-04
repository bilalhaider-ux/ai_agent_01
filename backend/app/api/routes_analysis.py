import os
import shutil
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.analysis_service import run_analysis
from app.services.file_service import save_upload
from app.services.rate_limit_service import rate_limiter

router = APIRouter(prefix="/api/v1")


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    executive_summary: str | None = None
    answers_to_query: str | None = None
    statistical_insights: list[str] = []
    recommended_actions: list[str] = []
    metrics: dict[str, Any] = {}
    grounding: dict[str, Any] | None = None
    generated_code: str | None = None
    charts: list[str] = []
    markdown_report: str | None = None
    html_report: str | None = None
    error: dict[str, str] | None = None


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze(
    request: Request,
    response: Response,
    query: str = Form(...),
    dataset: UploadFile = File(...),
    provider: str | None = Form(None),
    model: str | None = Form(None),
) -> AnalysisResponse:
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    dataset_path = await save_upload(dataset)

    quota_token = request.cookies.get("analysis_quota_token")
    issue_token = quota_token is None
    quota_token = quota_token or rate_limiter.issue_token()
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
    quota = rate_limiter.check_and_consume(client_ip, quota_token)
    response.headers["X-RateLimit-Limit"] = str(quota.limit)
    response.headers["X-RateLimit-Remaining"] = str(quota.remaining)
    response.headers["X-RateLimit-Reset"] = str(quota.reset_at)
    if issue_token:
        response.set_cookie(
            "analysis_quota_token",
            quota_token,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="lax",
            secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        )
    if not quota.allowed:
        shutil.rmtree(dataset_path.parent, ignore_errors=True)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Analysis limit reached. Please try again after the quota reset time.",
                "limit": quota.limit,
                "remaining": quota.remaining,
                "reset_at": quota.reset_at,
            },
            headers={
                "X-RateLimit-Limit": str(quota.limit),
                "X-RateLimit-Remaining": str(quota.remaining),
                "X-RateLimit-Reset": str(quota.reset_at),
            },
        )
    result = run_analysis(dataset_path, query.strip(), provider, model)
    if result["status"] == "failed":
        response_status = status.HTTP_429_TOO_MANY_REQUESTS if result.get("error", {}).get("type") == "ProviderRateLimitError" else status.HTTP_502_BAD_GATEWAY
        return JSONResponse(
            status_code=response_status,
            content=result,
            headers={
                "X-RateLimit-Limit": str(quota.limit),
                "X-RateLimit-Remaining": str(quota.remaining),
                "X-RateLimit-Reset": str(quota.reset_at),
            },
        )
    return AnalysisResponse(**result)