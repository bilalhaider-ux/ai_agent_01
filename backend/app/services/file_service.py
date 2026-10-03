"""Safe temporary storage for uploaded datasets."""

import os
import re
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".parquet", ".tsv", ".json", ".jsonl"}
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(50 * 1024 * 1024)))


def validate_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A dataset filename is required.")
    safe_name = Path(filename).name
    if safe_name != filename or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", safe_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset filename contains unsafe characters.")
    if Path(safe_name).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supported dataset types are CSV, XLSX, Parquet, TSV, JSON, and JSONL.")
    return safe_name


async def save_upload(upload: UploadFile) -> Path:
    filename = validate_filename(upload.filename)
    temporary_directory = Path(tempfile.mkdtemp(prefix="ai-agent-upload-"))
    destination = temporary_directory / filename
    size = 0
    try:
        with destination.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Dataset exceeds the {MAX_UPLOAD_BYTES} byte upload limit.")
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        temporary_directory.rmdir()
        raise
    return destination