from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.repositories import user_repository, role_repository
from app.schemas.user import UserCreate

from app.models.user import User

from app.core.security import create_access_token,create_refresh_token,get_claims,verify_refresh_token
from app.core.session_store import get_active_access_token,set_active_access_token
from app.core.auth_utils import blacklist_token,validate_access_token


password_hash = PasswordHash.recommended()


def signup(db: Session,user_data: UserCreate) -> User:

    existing_user = user_repository.get_user_by_email(db,user_data.email)

    if existing_user is not None:
        raise ValueError("Email already registered")

    role = role_repository.get_role_by_id(db,user_data.role_id)

    if role is None:
        raise ValueError("Role not found")

    hashed_password = password_hash.hash(user_data.password)

    return user_repository.signup(db,user_data,hashed_password)


def login(db: Session,email: str,password: str) -> tuple[str, str]:

    user = user_repository.get_user_by_email(db,email)

    if user is None:
        raise ValueError("Invalid email or password")

    password_valid = password_hash.verify(password,user.password)

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
            blacklist_token(old_access_token,old_claims)

    access_token = create_access_token(user_id,role_id)

    refresh_token = create_refresh_token(user_id,role_id)

    set_active_access_token(user_id,access_token)

    return access_token, refresh_token

def refresh_access_token(db: Session,access_token: str,refresh_token: str) -> tuple[str, str]:

    access_claims = validate_access_token(access_token)

    user_id = verify_refresh_token(refresh_token)

    if user_id is None:
        raise ValueError("Invalid or expired refresh token")

    access_user_id = access_claims["sub"]

    if access_user_id != user_id:
        raise ValueError("Token user mismatch")

    user = user_repository.get_user_by_id(db,user_id)

    if user is None:
        raise ValueError("User not found")

    if not user.is_active:
        raise ValueError("User account is inactive")

    blacklist_token(access_token,access_claims)

    new_access_token = create_access_token(str(user.id),str(user.role_id))

    new_refresh_token = create_refresh_token(str(user.id),str(user.role_id))

    set_active_access_token(str(user.id),new_access_token)

    return new_access_token, new_refresh_token

def logout(access_token: str) -> None:

    claims = validate_access_token(access_token)

    blacklist_token(access_token,claims)
