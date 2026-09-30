from typing import cast

from jose import JWTError

from app.core.exceptions import AuthenticationException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_claims,
    verify_refresh_token,
)
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.session_store import (
    blacklist_token,
    get_active_access_token,
    is_blacklisted,
    remove_active_refresh_token,
    set_active_access_token,
    set_active_refresh_token,
)


def validate_access_token(access_token: str) -> TokenClaims:
    if is_blacklisted(access_token):
        raise AuthenticationException("Access token has been revoked")

    try:
        claims = get_claims(access_token)
    except JWTError:
        raise AuthenticationException("Invalid access token") from None

    if claims.get("type") != "access":
        raise AuthenticationException("Invalid access token")

    return cast(TokenClaims, claims)


def issue_tokens(user_id: str, role_id: str) -> tuple[str, str]:
    access_token = create_access_token(user_id, role_id)
    refresh_token = create_refresh_token(user_id, role_id)

    refresh_claims = get_claims(refresh_token)
    set_active_refresh_token(str(refresh_claims["jti"]), float(refresh_claims["exp"]))

    set_active_access_token(user_id, access_token)

    return access_token, refresh_token


def revoke_old_access_token(user_id: str) -> None:
    old_access_token = get_active_access_token(user_id)
    if old_access_token is not None:
        try:
            old_claims = get_claims(old_access_token)
            blacklist_token(old_access_token, cast(TokenClaims, old_claims))
        except JWTError:
            pass


def revoke_refresh_session(refresh_token: str) -> None:
    refresh_claims = verify_refresh_token(refresh_token)
    if refresh_claims is not None:
        jti = str(refresh_claims["jti"])
        remove_active_refresh_token(jti)
