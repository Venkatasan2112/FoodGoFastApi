import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.auth_types import TokenClaims
from app.core.config import settings


def create_access_token(user_id: str, role_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": user_id,
        "role_id": role_id,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }

    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def create_refresh_token(user_id: str, role_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    payload = {
        "sub": user_id,
        "role_id": role_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }

    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def get_claims(token: str) -> TokenClaims:
    claims = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    return {
        "sub": str(claims["sub"]),
        "role_id": str(claims["role_id"]),
        "type": str(claims["type"]),
        "jti": str(claims["jti"]),
        "exp": float(claims["exp"]),
    }


def verify_access_token(token: str) -> TokenClaims | None:
    try:
        claims = get_claims(token)
        if claims["type"] != "access":
            return None
        return claims
    except JWTError:
        return None


def verify_refresh_token(token: str) -> str | None:
    try:
        claims = get_claims(token)
        if claims["type"] != "refresh":
            return None
        user_id = claims["sub"]
        if user_id == "":
            return None
        return user_id
    except JWTError:
        return None
