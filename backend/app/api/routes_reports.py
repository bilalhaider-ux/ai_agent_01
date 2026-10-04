from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.services.job_service import job_store

router = APIRouter(prefix="/api/v1/reports")


def report_or_404(analysis_id: str) -> dict:
    record = job_store.get(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis report was not found.")
    return record


@router.get("/{analysis_id}")
def report(analysis_id: str) -> dict:
    return report_or_404(analysis_id)


@router.get("/{analysis_id}/markdown", response_class=PlainTextResponse)
def markdown_report(analysis_id: str) -> str:
    return report_or_404(analysis_id).get("markdown_report", "")


@router.get("/{analysis_id}/html", response_class=HTMLResponse)
def html_report(analysis_id: str) -> str:
    return report_or_404(analysis_id).get("html_report", "")
