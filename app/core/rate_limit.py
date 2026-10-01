import logging

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from app.core.exceptions import ServiceUnavailableException
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

LOGIN_LIMIT = 5
SIGNUP_LIMIT = 3
WINDOW_SECONDS = 60


def _check_rate_limit(request: Request, action: str, limit: int) -> None:
    client_ip = (
        request.client.host
        if request.client is not None
        and request.client.host is not None
        and request.client.host != ""
        else "unknown"
    )
    key = f"auth:rate:{action}:{client_ip}"

    try:
        current = redis_client.incr(key)
        if current == 1:
            _ = redis_client.expire(key, WINDOW_SECONDS)
            ttl = WINDOW_SECONDS
        else:
            ttl = redis_client.ttl(key)
            if ttl == -1:
                _ = redis_client.expire(key, WINDOW_SECONDS)
                ttl = WINDOW_SECONDS
    except RedisError as e:
        logger.error("Redis unavailable for rate limiting: %s", e)
        raise ServiceUnavailableException(
            "Authentication service temporarily unavailable"
        ) from None

    if current > limit:
        retry_after = ttl if ttl > 0 else WINDOW_SECONDS
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def login_rate_limit(request: Request) -> None:
    _check_rate_limit(request, "login", LOGIN_LIMIT)


def signup_rate_limit(request: Request) -> None:
    _check_rate_limit(request, "signup", SIGNUP_LIMIT)
