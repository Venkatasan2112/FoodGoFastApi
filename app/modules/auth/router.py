from typing import TypedDict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth import service as auth_service
from app.modules.auth.dependencies import (
    get_bearer_token,
    get_refresh_token,
)
from app.modules.auth.schema import LoginRequest, LoginResponse
from app.modules.users.model import User
from app.modules.users.schema import UserCreate, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LogoutResponse(TypedDict):
    message: str


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def signup(user_data: UserCreate, db: Session = Depends(get_db)) -> User:  # noqa: B008
    try:
        return auth_service.signup(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),  # noqa: B008
) -> LoginResponse:
    try:
        access_token, refresh_token = auth_service.login(
            db, login_data.email, login_data.password
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    auth_service.set_refresh_cookie(response, refresh_token)

    return LoginResponse(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=LoginResponse)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),  # noqa: B008
) -> LoginResponse:
    access_token = get_bearer_token(request)
    refresh_token = get_refresh_token(request)

    try:
        new_access_token, new_refresh_token = auth_service.refresh_access_token(
            db, access_token, refresh_token
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    auth_service.set_refresh_cookie(response, new_refresh_token)

    return LoginResponse(access_token=new_access_token, token_type="bearer")


@router.post("/logout")
def logout(request: Request, response: Response) -> LogoutResponse:
    access_token = get_bearer_token(request)

    try:
        auth_service.logout(access_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    auth_service.delete_refresh_cookie(response)

    return {"message": "Logout successful"}
