from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.schemas import MessageResponse
from app.db.session import get_db
from app.modules.auth import cookie
from app.modules.auth import service as auth_service
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.dependencies import (
    get_bearer_token,
    get_optional_current_user,
    get_optional_refresh_token,
    get_refresh_token,
)
from app.modules.auth.schema import (
    LoginRequest,
    LoginResponse,
    SignupRequest,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

DBSession = Annotated[Session, Depends(get_db)]
AccessToken = Annotated[str, Depends(get_bearer_token)]
RefreshToken = Annotated[str, Depends(get_refresh_token)]
OptionalRefreshToken = Annotated[str | None, Depends(get_optional_refresh_token)]
OptionalCurrentUser = Annotated[TokenClaims | None, Depends(get_optional_current_user)]


@router.post(
    "/signup", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
def signup(
    user_data: SignupRequest,
    db: DBSession,
    current_user: OptionalCurrentUser = None,
) -> MessageResponse:
    auth_service.signup(db, user_data, current_user)
    return MessageResponse(message="User created successfully")


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    response: Response,
    db: DBSession,
) -> LoginResponse:
    access_token, refresh_token = auth_service.login(
        db, login_data.email, login_data.password
    )
    cookie.set_refresh_cookie(response, refresh_token)
    return LoginResponse(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=LoginResponse)
def refresh(
    response: Response,
    access_token: AccessToken,
    refresh_token: RefreshToken,
    db: DBSession,
) -> LoginResponse:
    new_access_token, new_refresh_token = auth_service.refresh_access_token(
        db, access_token, refresh_token
    )
    cookie.set_refresh_cookie(response, new_refresh_token)
    return LoginResponse(access_token=new_access_token, token_type="bearer")


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    access_token: AccessToken,
    refresh_token: OptionalRefreshToken = None,
) -> MessageResponse:
    auth_service.logout(access_token, refresh_token)
    cookie.delete_refresh_cookie(response)
    return MessageResponse(message="Logout successful")
