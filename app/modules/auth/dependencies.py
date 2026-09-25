from typing import cast
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import verify_access_token
from app.db.session import get_db
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.session_store import is_blacklisted
from app.modules.roles import repository as role_repository

REFRESH_COOKIE_NAME = "refresh_token"


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


def require_admin(
    current_user: TokenClaims = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> TokenClaims:
    role_id = UUID(current_user["role_id"])

    role = role_repository.get_role_by_id(db, role_id)

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Role not found"
        )

    if role.name != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user
