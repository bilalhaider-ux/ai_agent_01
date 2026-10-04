"""Persistent anonymous analysis quota backed by Upstash Redis."""

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass

from upstash_redis import Redis


@dataclass(frozen=True)
class QuotaResult:
    allowed: bool
    remaining: int
    reset_at: int
    limit: int


class AnalysisRateLimiter:
    def __init__(self) -> None:
        url = os.getenv("UPSTASH_REDIS_REST_URL")
        token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        self._redis = Redis(url=url, token=token) if url and token else None
        self._secret = os.getenv("RATE_LIMIT_SECRET")
        self._limit = int(os.getenv("MAX_REQUESTS_PER_HOUR", "5"))
        self._window_seconds = 60 * 60

    @property
    def enabled(self) -> bool:
        return self._redis is not None and bool(self._secret)

    def issue_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _key(self, identity: str) -> str:
        identity = identity.encode("utf-8")
        digest = hmac.new(self._secret.encode("utf-8"), identity, hashlib.sha256).hexdigest()
        return f"analysis-quota:{digest}"

    def _consume(self, key: str, now: int) -> int:
        cutoff = now - self._window_seconds
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, cutoff)
        pipe.zadd(key, {str(now) + ":" + secrets.token_hex(4): now})
        pipe.zcard(key)
        pipe.expire(key, self._window_seconds + 60)
        return int(pipe.exec()[2])

    def check_and_consume(self, ip_address: str, token: str) -> QuotaResult:
        if not self.enabled:
            return QuotaResult(True, self._limit, int(time.time()) + self._window_seconds, self._limit)

        now = int(time.time())
        ip_count = self._consume(self._key(f"ip:{ip_address}"), now)
        token_count = self._consume(self._key(f"token:{token}"), now)
        request_count = max(ip_count, token_count)
        reset_at = now + self._window_seconds
        return QuotaResult(
            allowed=request_count <= self._limit,
            remaining=max(0, self._limit - request_count),
            reset_at=reset_at,
            limit=self._limit,
        )


rate_limiter = AnalysisRateLimiter()