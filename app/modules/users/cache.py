import json
import logging
from typing import TypedDict, cast

from redis.exceptions import RedisError

from app.core.redis import redis_client

logger = logging.getLogger(__name__)

USERS_CACHE_KEY = "users:all"
USER_CACHE_PREFIX = "users:"
CACHE_TTL = 300


class UserCacheData(TypedDict):
    id: str
    name: str
    email: str
    phone: str | None
    role_id: str
    is_active: bool


def _user_cache_key(user_id: str) -> str:
    return f"{USER_CACHE_PREFIX}{user_id}"


def get_users_from_cache() -> list[UserCacheData] | None:
    try:
        data = redis_client.get(USERS_CACHE_KEY)
    except RedisError as exc:
        logger.warning("Redis unavailable while reading cache: %s", exc)
        return None

    if data is None:
        return None

    try:
        return cast(list[UserCacheData], json.loads(data))
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Malformed JSON in users cache: %s", exc)
        return None


def set_users_cache(users: list[UserCacheData]) -> None:
    try:
        _ = redis_client.set(USERS_CACHE_KEY, json.dumps(users), ex=CACHE_TTL)
    except RedisError as exc:
        logger.warning("Redis unavailable while writing cache: %s", exc)


def delete_users_cache() -> None:
    try:
        _ = redis_client.delete(USERS_CACHE_KEY)
    except RedisError as exc:
        logger.warning("Redis unavailable while deleting cache: %s", exc)


def get_user_from_cache(user_id: str) -> UserCacheData | None:
    try:
        data = redis_client.get(_user_cache_key(user_id))
    except RedisError as exc:
        logger.warning(
            "Redis unavailable while reading cache for user %s: %s", user_id, exc
        )
        return None

    if data is None:
        return None

    try:
        return cast(UserCacheData, json.loads(data))
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Malformed JSON in cache for user %s: %s", user_id, exc)
        return None


def set_user_cache(user: UserCacheData) -> None:
    user_id = user["id"]
    try:
        _ = redis_client.set(_user_cache_key(user_id), json.dumps(user), ex=CACHE_TTL)
    except RedisError as exc:
        logger.warning(
            "Redis unavailable while writing cache for user %s: %s", user_id, exc
        )


def delete_user_cache(user_id: str) -> None:
    try:
        _ = redis_client.delete(_user_cache_key(user_id))
    except RedisError as exc:
        logger.warning(
            "Redis unavailable while deleting cache for user %s: %s", user_id, exc
        )
