from typing import cast

from fastapi import Response
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_claims,
    verify_refresh_token,
)
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.schema import SignupRequest
from app.modules.auth.session_store import (
    blacklist_token,
    get_active_access_token,
    is_blacklisted,
    is_refresh_token_active,
    remove_active_refresh_token,
    set_active_access_token,
    set_active_refresh_token,
)
from app.modules.roles import repository as role_repository
from app.modules.users import repository as user_repository
from app.modules.users.model import User
from app.modules.users.schema import UserCreate

password_hash = PasswordHash.recommended()

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    refresh_cookie_max_age = settings.refresh_token_expire_days * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=refresh_cookie_max_age,
        path=REFRESH_COOKIE_PATH,
    )


def delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def validate_access_token(access_token: str) -> TokenClaims:
    if is_blacklisted(access_token):
        raise ValueError("Access token has been revoked")

    claims = get_claims(access_token)

    if claims.get("type") != "access":
        raise ValueError("Invalid access token")

    return cast(TokenClaims, claims)


def signup(db: Session, user_data: SignupRequest) -> User:
    existing_user = user_repository.get_user_by_email(db, user_data.email)

    if existing_user is not None:
        raise ValueError("Email already registered")

    role = role_repository.get_role_by_name(db, "USER")

    if role is None:
        raise ValueError("Role not found")

    hashed_password = password_hash.hash(user_data.password)

    user_create_data = UserCreate(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        phone=user_data.phone,
        role_id=role.id,
    )

    try:
        user = user_repository.signup(db, user_create_data, hashed_password)
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def login(db: Session, email: str, password: str) -> tuple[str, str]:
    user = user_repository.get_user_by_email(db, email)

    if user is None:
        raise ValueError("Invalid email or password")

    password_valid = password_hash.verify(password, user.password)

    if not password_valid:
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("User account is inactive")

    user_id = str(user.id)
    role_id = str(user.role_id)

    old_access_token = get_active_access_token(user_id)

    if old_access_token is not None:
        old_claims = get_claims(old_access_token)

        if old_claims is not None:
            blacklist_token(old_access_token, cast(TokenClaims, old_claims))

    access_token = create_access_token(user_id, role_id)
    refresh_token = create_refresh_token(user_id, role_id)

    refresh_claims = get_claims(refresh_token)
    set_active_refresh_token(str(refresh_claims["jti"]), float(refresh_claims["exp"]))

    set_active_access_token(user_id, access_token)

    return access_token, refresh_token


def refresh_access_token(
    db: Session, access_token: str, refresh_token: str
) -> tuple[str, str]:
    access_claims = validate_access_token(access_token)
    user_id = verify_refresh_token(refresh_token)

    if user_id is None:
        raise ValueError("Invalid or expired refresh token")

    refresh_claims = get_claims(refresh_token)
    jti = str(refresh_claims["jti"])

    if not is_refresh_token_active(jti):
        raise ValueError("Refresh token has been revoked or is not active")

    access_user_id = access_claims["sub"]

    if access_user_id != user_id:
        raise ValueError("Token user mismatch")

    user = user_repository.get_user_by_id(db, user_id)

    if user is None:
        raise ValueError("User not found")

    if not user.is_active:
        raise ValueError("User account is inactive")

    blacklist_token(access_token, access_claims)
    remove_active_refresh_token(jti)

    new_access_token = create_access_token(str(user.id), str(user.role_id))
    new_refresh_token = create_refresh_token(str(user.id), str(user.role_id))

    new_refresh_claims = get_claims(new_refresh_token)
    set_active_refresh_token(
        str(new_refresh_claims["jti"]), float(new_refresh_claims["exp"])
    )

    set_active_access_token(str(user.id), new_access_token)

    return new_access_token, new_refresh_token


def logout(access_token: str, refresh_token: str | None = None) -> None:
    claims = validate_access_token(access_token)
    blacklist_token(access_token, claims)

    if refresh_token is not None:
        try:
            refresh_claims = get_claims(refresh_token)
            if refresh_claims.get("type") == "refresh":
                jti = refresh_claims.get("jti")
                if jti is not None:
                    remove_active_refresh_token(str(jti))
        except Exception:  # noqa: BLE001, S110
            pass
