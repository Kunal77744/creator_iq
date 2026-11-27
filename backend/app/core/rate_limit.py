"""Rate-limiting utilities backed by Redis with a thread-safe in-memory fallback."""
from collections import defaultdict, deque
import os
import threading
import time

from fastapi import HTTPException, Request, status

from .redis import get_redis_client

# Thread lock and sliding-window buckets used when Redis is unavailable
_lock = threading.Lock()
_memory_buckets: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    """Clear in-memory rate-limit buckets (for tests)."""
    with _lock:
        _memory_buckets.clear()


def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    """Enforce a fixed/sliding window rate limit using Redis with in-memory fallback."""
    if os.getenv("DISABLE_RATE_LIMIT") == "1":
        return

    # Try Redis counter first for distributed rate limiting
    client = get_redis_client()
    if client is not None:
        try:
            redis_key = f"rl:{key}"
            count = client.incr(redis_key)
            if count == 1:
                client.expire(redis_key, window_seconds)
            if count > limit:
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again shortly.",
                )
            return
        except HTTPException:
            raise
        except Exception:
            pass

    # Fallback to an in-memory sliding window when Redis is unavailable
    now = time.monotonic()
    with _lock:
        bucket = _memory_buckets[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again shortly.",
            )
        bucket.append(now)


def rate_limit(scope: str, limit: int = 30, window_seconds: int = 60):
    """FastAPI dependency enforcing per-client-IP rate limits."""

    def _dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        check_rate_limit(f"{scope}:{ip}", limit=limit, window_seconds=window_seconds)

    return _dependency
