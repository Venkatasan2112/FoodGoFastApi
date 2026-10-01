from typing import cast
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException
from app.core.security import verify_access_token
from app.db.session import get_db
from app.modules.auth import authorization
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.cookie import REFRESH_COOKIE_NAME
from app.modules.auth.session_store import is_blacklisted


def get_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")

    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    scheme, separator, token = authorization.partition(" ")

    if separator != " " or scheme.lower() != "bearer" or token.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    return token.strip()


def get_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )

    return refresh_token


def get_optional_refresh_token(request: Request) -> str | None:
    return request.cookies.get(REFRESH_COOKIE_NAME)


def get_current_user(request: Request) -> TokenClaims:
    token = get_bearer_token(request)

    if is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has been revoked",
        )

    claims = verify_access_token(token)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    return cast(TokenClaims, claims)


def get_optional_current_user(request: Request) -> TokenClaims | None:
    auth_header = request.headers.get("Authorization")
    if auth_header is None or auth_header == "":
        return None

    return get_current_user(request)


def require_admin(
    current_user: TokenClaims = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> TokenClaims:
    try:
        role = authorization.resolve_caller_role(db, current_user)
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=e.detail
        ) from None

    if not authorization.is_admin_role(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user


def require_self_or_admin(
    user_id: UUID,
    current_user: TokenClaims = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> TokenClaims:
    if str(user_id) == current_user["sub"]:
        return current_user

    try:
        role = authorization.resolve_caller_role(db, current_user)
    except AuthorizationException as e:
        if e.detail == "Role not found":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user",
            ) from None
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=e.detail
        ) from None

    if role.name != authorization.ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )

    return current_user
