"""Redis client initialization and JSON cache helper functions."""
import json
import logging
from typing import Any, Optional

import redis

from ..config import REDIS_URL

log = logging.getLogger("creatoriq.redis")

# Lazily initialized shared Redis connection
_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Return a shared Redis client, or None if Redis is unavailable."""
    global _client
    if _client is None:
        try:
            _client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        except Exception as exc:
            log.warning("Failed to initialize Redis client: %s", exc)
            return None
    return _client


def redis_ping() -> bool:
    """Return True if Redis responds to PING, False otherwise."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        return bool(client.ping())
    except Exception:
        return False


def cache_get(key: str) -> Any:
    """Fetch and JSON-decode a cached value by key, returning None on miss or error."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as exc:
        log.warning("Redis cache_get failed for %s: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 120) -> None:
    """JSON-serialize and store a value in Redis with a TTL in seconds."""
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception as exc:
        log.warning("Redis cache_set failed for %s: %s", key, exc)


def cache_delete(key: str) -> None:
    """Delete a single cache key from Redis if present."""
    client = get_redis_client()
    if client is None:
        return
    try:
        client.delete(key)
    except Exception as exc:
        log.warning("Redis cache_delete failed for %s: %s", key, exc)


def cache_delete_prefix(prefix: str) -> None:
    """Scan and delete all Redis keys matching the given prefix."""
    client = get_redis_client()
    if client is None:
        return
    try:
        keys = list(client.scan_iter(match=f"{prefix}*"))
        if keys:
            client.delete(*keys)
    except Exception as exc:
        log.warning("Redis cache_delete_prefix failed for %s: %s", prefix, exc)
