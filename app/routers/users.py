from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_types import TokenClaims
from app.core.dependencies import get_current_user, require_admin
from app.core.user_cache import UserCacheData
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserProfileUpdate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/get-user-profile", response_model=UserResponse)
def get_user_profile(
    current_user: TokenClaims = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:

    try:
        user_id = current_user["sub"]

        return user_service.get_user_profile(db, user_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/update-user/{user_id}", response_model=UserResponse)
def update_user(
    user_data: UserProfileUpdate,
    user_id: UUID,
    current_user: TokenClaims = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:

    try:
        return user_service.update_user(db, user_id, user_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/get-user-by-id/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: UUID,
    current_user: TokenClaims = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserCacheData:

    try:
        return user_service.get_user_by_id(db, user_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/delete-user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    current_user: TokenClaims = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:

    try:
        user_service.delete_user(db, user_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/get-all-users", response_model=list[UserResponse])
def get_all_users(
    current_user: TokenClaims = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[UserCacheData]:

    try:
        return user_service.get_all_users(db)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
