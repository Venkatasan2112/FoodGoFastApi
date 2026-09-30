from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException
from app.modules.auth.auth_types import TokenClaims
from app.modules.roles import repository as role_repository

DEFAULT_SIGNUP_ROLE = "USER"
ADMIN_ROLE = "ADMIN"
ALLOWED_ADMIN_ROLES = frozenset({ADMIN_ROLE, "SUPER_ADMIN"})


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

        caller_role_id = UUID(current_user["role_id"])
        caller_role = role_repository.get_role_by_id(db, caller_role_id)

        if caller_role is None or caller_role.name not in ALLOWED_ADMIN_ROLES:
            raise AuthorizationException("Role assignment requires admin access")

    return requested_role.id
