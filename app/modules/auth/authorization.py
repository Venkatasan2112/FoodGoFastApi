from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException
from app.modules.auth.auth_types import TokenClaims
from app.modules.roles import repository as role_repository
from app.modules.roles.model import Role

DEFAULT_SIGNUP_ROLE = "USER"
ADMIN_ROLE = "ADMIN"
ALLOWED_ADMIN_ROLES = frozenset({ADMIN_ROLE, "SUPER_ADMIN"})


def resolve_caller_role(db: Session, current_user: TokenClaims) -> Role:
    role_id_str = current_user.get("role_id")
    if role_id_str is None or role_id_str == "":
        raise AuthorizationException("Role information missing")

    try:
        role_id = UUID(role_id_str)
    except (ValueError, TypeError):
        raise AuthorizationException("Invalid role ID format")

    role = role_repository.get_role_by_id(db, role_id)
    if role is None:
        raise AuthorizationException("Role not found")

    return role


def is_admin_role(role: Role) -> bool:
    return role.name in ALLOWED_ADMIN_ROLES


def resolve_signup_role(
    db: Session,
    role_id: UUID | None,
    current_user: TokenClaims | None,
) -> UUID:
    if role_id is None:
        role = role_repository.get_role_by_name(db, DEFAULT_SIGNUP_ROLE)
        if role is None:
            raise NotFoundException("Role not found")
        return role.id

    requested_role = role_repository.get_role_by_id(db, role_id)
    if requested_role is None:
        raise NotFoundException("Requested role not found")

    if requested_role.name != ADMIN_ROLE:
        if current_user is None:
            raise AuthorizationException("Role assignment requires admin access")

        caller_role = resolve_caller_role(db, current_user)

        if not is_admin_role(caller_role):
            raise AuthorizationException("Role assignment requires admin access")

    return requested_role.id
