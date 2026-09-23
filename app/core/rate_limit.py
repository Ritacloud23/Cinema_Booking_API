from fastapi import HTTPException, status

from app.cache.redis import redis_client


def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
):
    current_count = redis_client.incr(key)

    if current_count == 1:
        redis_client.expire(key, window_seconds)

    if current_count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={
                "Retry-After": str(window_seconds),
            },
        )