from datetime import datetime, timedelta, timezone
import uuid

from jose import JWTError, jwt

from app.core.auth_types import TokenClaims


SECRET_KEY = "foodgo-super-secret-key-change-this"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str, role_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {"sub": user_id, "role_id": role_id, "type": "access", "jti": str(uuid.uuid4()), "exp": expire}

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str, role_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {"sub": user_id, "role_id": role_id, "type": "refresh", "jti": str(uuid.uuid4()), "exp": expire}

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_claims(token: str) -> TokenClaims:
    claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return {"sub": str(claims["sub"]), "role_id": str(claims["role_id"]), "type": str(claims["type"]), "jti": str(claims["jti"]), "exp": float(claims["exp"])}


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