import logging
import time
from collections import defaultdict
from threading import Lock

from core import config

logger = logging.getLogger("aiwiki.rate_limit")


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            window_start = now - self.window_seconds
            hits = [t for t in self._hits[key] if t > window_start]
            if len(hits) >= self.limit:
                self._hits[key] = hits
                return False
            hits.append(now)
            self._hits[key] = hits
            return True

    def retry_after(self, key: str) -> int:
        now = time.time()
        with self._lock:
            hits = self._hits.get(key, [])
            if not hits:
                return 0
            oldest = min(hits)
            return max(1, int(self.window_seconds - (now - oldest)))


class RedisRateLimiter:
    def __init__(self, redis_url: str, limit: int, window_seconds: int = 60):
        import redis

        self._redis = redis.from_url(redis_url, decode_responses=True)
        self.limit = limit
        self.window_seconds = window_seconds
        self._redis.ping()

    def allow(self, key: str) -> bool:
        bucket = f"aiwiki:rl:{key}:{int(time.time() // self.window_seconds)}"
        count = self._redis.incr(bucket)
        if count == 1:
            self._redis.expire(bucket, self.window_seconds + 1)
        return count <= self.limit

    def retry_after(self, key: str) -> int:
        bucket = f"aiwiki:rl:{key}:{int(time.time() // self.window_seconds)}"
        ttl = self._redis.ttl(bucket)
        return max(1, ttl if ttl and ttl > 0 else self.window_seconds)


def _build_limiter(limit: int) -> RateLimiter | RedisRateLimiter:
    if config.REDIS_URL:
        try:
            limiter = RedisRateLimiter(config.REDIS_URL, limit)
            logger.info("Rate limiter using Redis")
            return limiter
        except Exception as exc:
            logger.warning("Redis rate limiter unavailable, using in-memory fallback: %s", exc)
    return RateLimiter(limit)


def rate_limit_backend() -> str:
    if config.REDIS_URL:
        try:
            import redis

            client = redis.from_url(config.REDIS_URL, decode_responses=True)
            client.ping()
            return "redis"
        except Exception:
            return "memory"
    return "memory"


api_rate_limiter = _build_limiter(config.EXTERNAL_RATE_LIMIT)
registration_rate_limiter = _build_limiter(config.REGISTRATION_RATE_LIMIT)
