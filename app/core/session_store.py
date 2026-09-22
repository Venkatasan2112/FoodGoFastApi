from threading import Lock

_active_access_tokens: dict[str, str] = {}

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
