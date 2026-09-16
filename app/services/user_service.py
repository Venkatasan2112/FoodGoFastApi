from app.core.user_cache import UserCacheData
from sqlalchemy import UUID
from sqlalchemy.orm import Session

from app.repositories import user_repository
from app.schemas.user import UserProfileUpdate
from app.core.user_cache import get_users_from_cache, set_users_cache, delete_users_cache, get_user_from_cache, set_user_cache, delete_user_cache

from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user import User


def get_user_profile(db: Session, user_id: str) -> User:

    user = user_repository.get_user_by_id(db, user_id)

    if user is None:
        raise ValueError("User not found")

    if not user.is_active:
        raise ValueError("User account is inactive")

    return user


def update_user(db: Session,user_id: str | UUID,user_data: UserProfileUpdate) -> User:

    user = user_repository.get_user_by_id(db, user_id)

    if user is None:
        raise ValueError("User not found")

    if not user.is_active:
        raise ValueError("User account is inactive")

    update_data = user_data.model_dump(exclude_unset=True,exclude_none=True)

    if len(update_data) == 0:
        return user

    updated_user = user_repository.update_user(db,user,update_data)

    delete_users_cache()
    delete_user_cache(str(user_id))

    return updated_user

def get_user_by_id(db: Session,user_id: str | UUID) -> UserCacheData:

    cached_user = get_user_from_cache(str(user_id))

    if cached_user is not None:
        return cached_user

    user = user_repository.get_user_by_id(db, user_id)

    if user is None:
        raise ValueError("User not found")

    if not user.is_active:
        raise ValueError("User account is inactive")

    user_data: UserCacheData = {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role_id": str(user.role_id),
        "is_active": user.is_active,
    }

    set_user_cache(user_data)

    return user_data


def delete_user(db: Session,user_id: str | UUID) -> None:

    user = user_repository.get_user_by_id(db, user_id)

    if user is None:
        raise ValueError("User not found")

    if not user.is_active:
        raise ValueError("User account is inactive")

    user_repository.delete_user(db, user)

    delete_users_cache()
    delete_user_cache(str(user_id))



def get_all_users(db: Session) -> list[UserCacheData]:
    cached_users = get_users_from_cache()

    if cached_users is not None:
        return cached_users

    users = user_repository.get_all_users(db)

    users_data: list[UserCacheData] = [
        {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role_id": str(user.role_id),
            "is_active": user.is_active,
        }
        for user in users
    ]

    set_users_cache(users_data)

    return users_data
