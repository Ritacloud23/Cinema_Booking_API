from app.cache.redis import redis_client
from app.core.rate_limit import check_rate_limit


def test_rate_limit_allows_requests():
    key = "test:rate_limit:allows"

    redis_client.delete(key)

    for _ in range(5):
        check_rate_limit(
            key=key,
            limit=5,
            window_seconds=60,
        )

    assert int(redis_client.get(key)) == 5

    redis_client.delete(key)


def test_rate_limit_blocks_after_limit():
    key = "test:rate_limit:blocks"

    redis_client.delete(key)

    for _ in range(5):
        check_rate_limit(
            key=key,
            limit=5,
            window_seconds=60,
        )

    try:
        check_rate_limit(
            key=key,
            limit=5,
            window_seconds=60,
        )
        assert False, "Expected rate limiter to block the request"
    except Exception as exc:
        assert exc.status_code == 429
        assert exc.headers["Retry-After"] == "60"

    redis_client.delete(key)