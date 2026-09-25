from typing import TypedDict


class TokenClaims(TypedDict):
    sub: str
    role_id: str
    type: str
    jti: str
    exp: float
