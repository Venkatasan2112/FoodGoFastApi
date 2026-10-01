from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthenticationException,
    ConflictException,
    NotFoundException,
)
from app.core.security import verify_refresh_token
from app.modules.auth import authorization, token_service
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.schema import SignupRequest
from app.modules.auth.session_store import (
    blacklist_token,
    is_refresh_token_active,
    remove_active_refresh_token,
)
from app.modules.users import repository as user_repository
from app.modules.users.cache import delete_users_cache
from app.modules.users.schema import UserCreate

password_hash = PasswordHash.recommended()


def signup(
    db: Session, user_data: SignupRequest, current_user: TokenClaims | None = None
) -> None:
    existing_user = user_repository.get_user_by_email(db, user_data.email)

    if existing_user is not None:
        raise ConflictException("Email already registered")

    role_id = authorization.resolve_signup_role(db, user_data.role_id, current_user)

    hashed_password = password_hash.hash(user_data.password)

    user_create_data = UserCreate(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        phone=user_data.phone,
        role_id=role_id,
    )

    try:
        _ = user_repository.signup(db, user_create_data, hashed_password)
        db.commit()
    except Exception:
        db.rollback()
        raise

    delete_users_cache()


def login(db: Session, email: str, password: str) -> tuple[str, str]:
    user = user_repository.get_user_by_email(db, email)

    if user is None:
        raise AuthenticationException("Invalid email or password")

    password_valid = password_hash.verify(password, user.password)

    if not password_valid:
        raise AuthenticationException("Invalid email or password")

    if not user.is_active:
        raise AuthenticationException("User account is inactive")

    user_id = str(user.id)
    role_id = str(user.role_id)

    token_service.revoke_old_access_token(user_id)

    return token_service.issue_tokens(user_id, role_id)


def refresh_access_token(
    db: Session, access_token: str, refresh_token: str
) -> tuple[str, str]:
    access_claims = token_service.validate_access_token(access_token)

    refresh_claims = verify_refresh_token(refresh_token)
    if refresh_claims is None:
        raise AuthenticationException("Invalid or expired refresh token")

    jti = str(refresh_claims["jti"])
    user_id = str(refresh_claims["sub"])

    if not is_refresh_token_active(jti):
        raise AuthenticationException("Refresh token has been revoked or is not active")

    access_user_id = access_claims["sub"]

    if access_user_id != user_id:
        raise AuthenticationException("Token user mismatch")

    user = user_repository.get_user_by_id(db, user_id)

    if user is None:
        raise NotFoundException("User not found")

    if not user.is_active:
        raise AuthenticationException("User account is inactive")

    blacklist_token(access_token, access_claims)
    remove_active_refresh_token(jti)

    return token_service.issue_tokens(str(user.id), str(user.role_id))


def logout(access_token: str, refresh_token: str | None = None) -> None:
    claims = token_service.validate_access_token(access_token)
    blacklist_token(access_token, claims)

    if refresh_token is not None:
        token_service.revoke_refresh_session(refresh_token)
