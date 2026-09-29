from typing import TypedDict

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.schemas import MessageResponse
from app.db.session import get_db
from app.modules.auth import service as auth_service
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.dependencies import (
    get_bearer_token,
    get_optional_current_user,
    get_refresh_token,
)
from app.modules.auth.schema import (
    LoginRequest,
    LoginResponse,
    SignupRequest,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LogoutResponse(TypedDict):
    message: str


@router.post(
    "/signup", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
def signup(
    user_data: SignupRequest,
    current_user: TokenClaims | None = Depends(get_optional_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> MessageResponse:
    _ = auth_service.signup(db, user_data, current_user)
    return MessageResponse(message="User created successfully")


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),  # noqa: B008
) -> LoginResponse:
    access_token, refresh_token = auth_service.login(
        db, login_data.email, login_data.password
    )

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

    new_access_token, new_refresh_token = auth_service.refresh_access_token(
        db, access_token, refresh_token
    )

    auth_service.set_refresh_cookie(response, new_refresh_token)

    return LoginResponse(access_token=new_access_token, token_type="bearer")


@router.post("/logout")
def logout(request: Request, response: Response) -> LogoutResponse:
    access_token = get_bearer_token(request)
    refresh_token = request.cookies.get("refresh_token")

    auth_service.logout(access_token, refresh_token)

    auth_service.delete_refresh_cookie(response)

    return {"message": "Logout successful"}
