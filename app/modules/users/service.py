from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationException, NotFoundException
from app.modules.users import repository as user_repository
from app.modules.users.cache import (
    UserCacheData,
    delete_user_cache,
    delete_users_cache,
    get_user_from_cache,
    get_users_from_cache,
    set_user_cache,
    set_users_cache,
)
from app.modules.users.model import User
from app.modules.users.schema import UpdateUserRequest


def _get_active_user(db: Session, user_id: str | UUID) -> User:
    user = user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundException("User not found")
    if not user.is_active:
        raise AuthenticationException("User account is inactive")
    return user


def _to_cache_data(user: User) -> UserCacheData:
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role_id": str(user.role_id),
        "is_active": user.is_active,
    }


def _invalidate_user_cache(user_id: str | UUID) -> None:
    delete_users_cache()
    delete_user_cache(str(user_id))


def get_user_profile(db: Session, user_id: str) -> User:
    return _get_active_user(db, user_id)


def update_user(db: Session, user_id: str | UUID, user_data: UpdateUserRequest) -> User:
    user = _get_active_user(db, user_id)
    update_data = user_data.model_dump(exclude_unset=True, exclude_none=True)

    if not bool(update_data):
        return user

    try:
        updated_user = user_repository.update_user(db, user, update_data)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(updated_user)
    _invalidate_user_cache(user_id)
    return updated_user


def get_user_by_id(db: Session, user_id: str | UUID) -> UserCacheData:
    user_id_str = str(user_id)
    cached_user = get_user_from_cache(user_id_str)
    if cached_user is not None:
        return cached_user

    user = _get_active_user(db, user_id)
    user_data = _to_cache_data(user)

    set_user_cache(user_data)
    return user_data


def delete_user(db: Session, user_id: str | UUID) -> None:
    user = _get_active_user(db, user_id)

    try:
        user_repository.delete_user(db, user)
        db.commit()
    except Exception:
        db.rollback()
        raise

    _invalidate_user_cache(user_id)


def get_all_users(db: Session) -> list[UserCacheData]:
    cached_users = get_users_from_cache()
    if cached_users is not None:
        return cached_users

    users = user_repository.get_all_users(db)
    users_data = [_to_cache_data(user) for user in users]

    set_users_cache(users_data)
    return users_data
