from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.analysis_service import run_analysis
from app.services.file_service import save_upload

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
async def analyze(query: str = Form(...), dataset: UploadFile = File(...), provider: str | None = Form(None), model: str | None = Form(None)) -> AnalysisResponse:
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")
    dataset_path = await save_upload(dataset)
    result = run_analysis(dataset_path, query.strip(), provider, model)
    if result["status"] == "failed":
        response_status = status.HTTP_429_TOO_MANY_REQUESTS if result.get("error", {}).get("type") == "ProviderRateLimitError" else status.HTTP_502_BAD_GATEWAY
        return JSONResponse(status_code=response_status, content=result)
    return AnalysisResponse(**result)