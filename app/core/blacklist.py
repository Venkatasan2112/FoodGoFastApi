from datetime import datetime, timezone
from threading import Lock


_blacklisted_tokens: dict[str, float] = {}

_lock = Lock()


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
