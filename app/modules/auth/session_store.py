import logging
from datetime import datetime, timezone

import redis
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.redis import redis_client
from app.modules.auth.auth_types import TokenClaims

logger = logging.getLogger(__name__)


def set_active_access_token(user_id: str, access_token: str) -> None:
    try:
        claims = jwt.get_unverified_claims(access_token)
        expiry = claims.get("exp")
        if expiry is not None:
            now = datetime.now(timezone.utc).timestamp()
            ttl = int(float(expiry) - now)
            if ttl > 0:
                _ = redis_client.setex(f"auth:active:{user_id}", ttl, access_token)
    except (redis.RedisError, JWTError) as e:
        logger.error(f"Failed to set active token in Redis: {e}")


def get_active_access_token(user_id: str) -> str | None:
    try:
        token = redis_client.get(f"auth:active:{user_id}")
        if token is None:
            return None
        return str(token)
    except redis.RedisError as e:
        logger.error(f"Failed to get active token from Redis: {e}")
        return None


def remove_active_access_token(user_id: str) -> None:
    try:
        _ = redis_client.delete(f"auth:active:{user_id}")
    except redis.RedisError as e:
        logger.error(f"Failed to remove active token from Redis: {e}")


def is_blacklisted(token: str) -> bool:
    try:
        claims = jwt.get_unverified_claims(token)
    except JWTError:
        return False

    jti = claims.get("jti")
    if jti is None or jti == "":
        return False

    try:
        return bool(redis_client.exists(f"auth:blacklist:{jti}"))
    except redis.RedisError as e:
        logger.error(f"Redis error during blacklist check: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )


def blacklist_token(token: str, claims: TokenClaims) -> None:
    jti = claims.get("jti")
    expiry = claims.get("exp")
    if jti is None or jti == "" or expiry is None:
        return

    now = datetime.now(timezone.utc).timestamp()
    ttl = int(float(expiry) - now)

    if ttl > 0:
        try:
            _ = redis_client.setex(f"auth:blacklist:{jti}", ttl, "1")
        except redis.RedisError as e:
            logger.error(f"Failed to blacklist token in Redis: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )


def set_active_refresh_token(jti: str, expiry: float) -> None:
    now = datetime.now(timezone.utc).timestamp()
    ttl = int(expiry - now)
    if ttl > 0:
        try:
            _ = redis_client.setex(f"auth:refresh:{jti}", ttl, "1")
        except redis.RedisError as e:
            logger.error(f"Failed to set active refresh token in Redis: {e}")


def is_refresh_token_active(jti: str) -> bool:
    try:
        return bool(redis_client.exists(f"auth:refresh:{jti}"))
    except redis.RedisError as e:
        logger.error(f"Redis error during refresh token check: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )


def remove_active_refresh_token(jti: str) -> None:
    try:
        _ = redis_client.delete(f"auth:refresh:{jti}")
    except redis.RedisError as e:
        logger.error(f"Failed to remove active refresh token from Redis: {e}")
