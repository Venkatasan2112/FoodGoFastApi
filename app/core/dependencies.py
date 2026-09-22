from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth_types import TokenClaims
from app.core.blacklist import is_blacklisted
from app.core.security import verify_access_token
from app.db.session import get_db
from app.repositories import role_repository


def get_current_user(request: Request) -> TokenClaims:
    authorization = request.headers.get("Authorization")
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization[7:].strip()
    if token == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

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

    return claims


def require_admin(
    current_user: TokenClaims = Depends(get_current_user), db: Session = Depends(get_db)
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
