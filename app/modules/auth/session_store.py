from datetime import datetime, timezone
from threading import Lock

from app.modules.auth.auth_types import TokenClaims

_active_access_tokens: dict[str, str] = {}
_blacklisted_tokens: dict[str, float] = {}
_lock = Lock()


def set_active_access_token(user_id: str, access_token: str) -> None:
    with _lock:
        _active_access_tokens[user_id] = access_token


def get_active_access_token(user_id: str) -> str | None:
    with _lock:
        return _active_access_tokens.get(user_id)


def remove_active_access_token(user_id: str) -> None:
    with _lock:
        _ = _active_access_tokens.pop(user_id, None)


def blacklist(token: str, expiry: datetime) -> None:
    with _lock:
        _blacklisted_tokens[token] = expiry.timestamp()


def is_blacklisted(token: str) -> bool:
    now = datetime.now(timezone.utc).timestamp()

    with _lock:
        expired_tokens = [
            token_key
            for token_key, expiry in _blacklisted_tokens.items()
            if expiry <= now
        ]

        for token_key in expired_tokens:
            del _blacklisted_tokens[token_key]

        return token in _blacklisted_tokens


def blacklist_token(token: str, claims: TokenClaims) -> None:
    expiry = claims.get("exp")
    if expiry is None:
        return
    expiry_datetime = datetime.fromtimestamp(expiry, tz=timezone.utc)
    blacklist(token, expiry_datetime)
