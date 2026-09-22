from typing import TypedDict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.auth_utils import (
    delete_refresh_cookie,
    get_bearer_token,
    get_refresh_token,
    raise_auth_error,
    set_refresh_cookie,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LogoutResponse(TypedDict):
    message: str


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def signup(user_data: UserCreate, db: Session = Depends(get_db)) -> User:
    try:
        return auth_service.signup(db, user_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> LoginResponse:

    try:
        access_token, refresh_token = auth_service.login(
            db, login_data.email, login_data.password
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    set_refresh_cookie(response, refresh_token)

    return LoginResponse(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=LoginResponse)
def refresh(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> LoginResponse:

    access_token = get_bearer_token(request)

    refresh_token = get_refresh_token(request)

    try:
        new_access_token, new_refresh_token = auth_service.refresh_access_token(
            db, access_token, refresh_token
        )

    except ValueError as e:
        raise_auth_error(e)

    set_refresh_cookie(response, new_refresh_token)

    return LoginResponse(access_token=new_access_token, token_type="bearer")


@router.post("/logout")
def logout(request: Request, response: Response) -> LogoutResponse:

    access_token = get_bearer_token(request)

    try:
        auth_service.logout(access_token)

    except ValueError as e:
        raise_auth_error(e)

    delete_refresh_cookie(response)

    return {"message": "Logout successful"}
