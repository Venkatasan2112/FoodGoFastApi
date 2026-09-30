from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.schemas import MessageResponse
from app.db.session import get_db
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.dependencies import (
    get_current_user,
    require_admin,
    require_self_or_admin,
)
from app.modules.users import service as user_service
from app.modules.users.cache import UserCacheData
from app.modules.users.model import User
from app.modules.users.schema import (
    UpdateUserRequest,
    UserProfileResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/get-user-profile", response_model=UserProfileResponse)
def get_user_profile(
    current_user: TokenClaims = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    return user_service.get_user_profile(db, current_user["sub"])


@router.put(
    "/update-user/{user_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_self_or_admin)],
)
def update_user(
    user_data: UpdateUserRequest,
    user_id: UUID,
    db: Session = Depends(get_db),  # noqa: B008
) -> MessageResponse:
    _ = user_service.update_user(db, user_id, user_data)
    return MessageResponse(message="User updated successfully")


@router.get(
    "/get-user-by-id/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
def get_user_by_id(
    user_id: UUID,
    db: Session = Depends(get_db),  # noqa: B008
) -> UserCacheData:
    return user_service.get_user_by_id(db, user_id)


@router.delete(
    "/delete-user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    user_service.delete_user(db, user_id)


@router.get(
    "/get-all-users",
    response_model=list[UserResponse],
    dependencies=[Depends(require_admin)],
)
def get_all_users(
    db: Session = Depends(get_db),  # noqa: B008
) -> list[UserCacheData]:
    return user_service.get_all_users(db)
