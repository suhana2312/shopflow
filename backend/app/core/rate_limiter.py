import time
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from app.core.redis import redis_client
from app.core.config import settings
from app.core.logging import logger

class RateLimiter:
    """
    Sliding window rate limiter using Redis sorted sets (or in-memory timestamps fallback).
    Prevents abuse on public endpoints, checkout, and authentication.
    """
    def __init__(self, requests_per_minute: int, key_prefix: str = "rate"):
        self.requests_per_minute = requests_per_minute
        self.key_prefix = key_prefix
        self._memory_windows: dict = {}

    def __call__(self, request: Request):
        now = time.time()
        window_start = now - 60.0

        # Identify client: either user_id from state or client IP
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            identifier = f"user:{user_id}"
            limit = self.requests_per_minute
        else:
            client_host = request.client.host if request.client else "127.0.0.1"
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                client_host = forwarded.split(",")[0].strip()
            identifier = f"ip:{client_host}"
            limit = min(self.requests_per_minute, settings.RATE_LIMIT_PER_MINUTE_IP)

        key = f"{self.key_prefix}:{identifier}"

        # If Redis is active, use Redis ZSET or simple counter
        if redis_client._is_connected and redis_client._client:
            try:
                pipe = redis_client._client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, 60)
                _, _, current_count, _ = pipe.execute()

                if current_count > limit:
                    logger.warning(f"Rate limit exceeded for {identifier} on {request.url.path}: {current_count}/{limit}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit exceeded. Maximum {limit} requests per minute allowed.",
                            "details": {"limit": limit, "current": current_count}
                        }
                    )
                return
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Redis rate-limit query failed ({e}), falling back to in-memory window.")

        # In-memory sliding window fallback
        timestamps = self._memory_windows.get(key, [])
        # Prune expired timestamps
        timestamps = [ts for ts in timestamps if ts > window_start]
        timestamps.append(now)
        self._memory_windows[key] = timestamps

        if len(timestamps) > limit:
            logger.warning(f"In-memory rate limit exceeded for {identifier} on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Maximum {limit} requests per minute allowed.",
                    "details": {"limit": limit, "current": len(timestamps)}
                }
            )

# Common rate limiter instances
standard_rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE_USER, key_prefix="standard")
auth_rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_AUTH_PER_MINUTE, key_prefix="auth")
checkout_rate_limiter = RateLimiter(requests_per_minute=15, key_prefix="checkout")
