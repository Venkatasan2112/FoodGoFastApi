import json
from typing import TypedDict, cast

from app.core.redis import redis_client


USERS_CACHE_KEY = "users:all"
USER_CACHE_PREFIX = "users:"
USERS_CACHE_TTL = 300


class UserCacheData(TypedDict):
    id: str
    name: str
    email: str
    phone: str | None
    role_id: str
    is_active: bool


def get_users_from_cache() -> list[UserCacheData] | None:
    data = redis_client.get(USERS_CACHE_KEY)

    if data is None:
        return None

    return cast(list[UserCacheData], json.loads(data))


def set_users_cache(users: list[UserCacheData]) -> None:
    _ = redis_client.set(USERS_CACHE_KEY,json.dumps(users),ex=USERS_CACHE_TTL)


def delete_users_cache() -> None:
    _ = redis_client.delete(USERS_CACHE_KEY)


def get_user_from_cache(user_id: str) -> UserCacheData | None:
    data = redis_client.get(f"{USER_CACHE_PREFIX}{user_id}")

    if data is None:
        return None

    return cast(UserCacheData, json.loads(data))


def set_user_cache(user: UserCacheData) -> None:
    _ = redis_client.set(
        f"{USER_CACHE_PREFIX}{user['id']}",
        json.dumps(user),
        ex=USERS_CACHE_TTL
    )


def delete_user_cache(user_id: str) -> None:
    _ = redis_client.delete(
        f"{USER_CACHE_PREFIX}{user_id}"
    )
