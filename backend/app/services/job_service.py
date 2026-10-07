"""Redis-backed analysis job state with a local fallback for development."""

import json
import os
import threading
import uuid
import base64
import zlib
from datetime import datetime, timezone
from typing import Any, Callable

from upstash_redis import Redis

_LOCAL_JOBS: dict[str, dict[str, Any]] = {}
_LOCAL_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnalysisJobStore:
    def __init__(self) -> None:
        url = os.getenv("UPSTASH_REDIS_REST_URL")
        token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        self._redis = Redis(url=url, token=token) if url and token else None
        self._prefix = os.getenv("ANALYSIS_JOB_KEY_PREFIX", "analysis-job:")
        self._ttl = int(os.getenv("ANALYSIS_JOB_TTL_SECONDS", str(24 * 60 * 60)))

    def _key(self, analysis_id: str) -> str:
        return f"{self._prefix}{analysis_id}"

    def _write(self, record: dict[str, Any]) -> None:
        if self._redis:
            payload = base64.b64encode(zlib.compress(json.dumps(record).encode("utf-8"), level=4)).decode("ascii")
            self._redis.set(self._key(record["analysis_id"]), f"z:{payload}", ex=self._ttl)
            return
        with _LOCAL_LOCK:
            _LOCAL_JOBS[record["analysis_id"]] = record.copy()

    def _read(self, analysis_id: str) -> dict[str, Any] | None:
        if self._redis:
            value = self._redis.get(self._key(analysis_id))
            if not value:
                return None
            if isinstance(value, str) and value.startswith("z:"):
                raw = base64.b64decode(value[2:])
                return json.loads(zlib.decompress(raw).decode("utf-8"))
            return json.loads(value) if isinstance(value, str) else value
        with _LOCAL_LOCK:
            value = _LOCAL_JOBS.get(analysis_id)
            return value.copy() if value else None

    def create(self) -> dict[str, Any]:
        record = {
            "analysis_id": str(uuid.uuid4()),
            "status": "queued",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self._write(record)
        return record

    def update(self, analysis_id: str, **changes: Any) -> dict[str, Any]:
        record = self._read(analysis_id) or {"analysis_id": analysis_id}
        record.update(changes)
        record["updated_at"] = _now()
        self._write(record)
        return record

    def get(self, analysis_id: str) -> dict[str, Any] | None:
        return self._read(analysis_id)

    def run(self, analysis_id: str, task: Callable[[], dict[str, Any]]) -> None:
        self.update(analysis_id, status="running")
        try:
            result = task()
            result = {key: value for key, value in result.items() if key != "analysis_id"}
            self.update(analysis_id, **result)
        except Exception as exc:
            self.update(analysis_id, status="failed", error={"type": type(exc).__name__, "message": str(exc)})


job_store = AnalysisJobStore()
