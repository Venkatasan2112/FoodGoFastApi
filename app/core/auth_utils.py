from datetime import datetime, timezone
from typing import NoReturn

from fastapi import HTTPException, Request, Response, status

from app.core.blacklist import blacklist, is_blacklisted
from app.core.auth_types import TokenClaims
from app.core.security import get_claims


REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60


def get_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")

    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authorization header missing")

    scheme, separator, token = authorization.partition(" ")

    if separator != " " or scheme.lower() != "bearer" or token.strip() == "":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid authorization header")

    return token.strip()


def get_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Missing refresh token")

    return refresh_token


def set_refresh_cookie(response: Response,refresh_token: str) -> None:

    response.set_cookie(key=REFRESH_COOKIE_NAME,value=refresh_token,httponly=True,secure=False,samesite="lax",max_age=REFRESH_COOKIE_MAX_AGE,path=REFRESH_COOKIE_PATH)


def delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME,path=REFRESH_COOKIE_PATH)


def raise_auth_error(error: ValueError) -> NoReturn:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=str(error))


def raise_conflict_error(error: ValueError) -> NoReturn:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=str(error))


def blacklist_token(token: str,claims: TokenClaims) -> None:

    expiry = claims.get("exp")

    if expiry is None:
        return

    expiry_datetime = datetime.fromtimestamp(expiry,tz=timezone.utc)

    blacklist(token,expiry_datetime)


def validate_access_token(access_token: str) -> TokenClaims:

    if is_blacklisted(access_token):
        raise ValueError("Access token has been revoked")

    claims = get_claims(access_token)

    if claims.get("type") != "access":
        raise ValueError("Invalid access token")

    return claims
