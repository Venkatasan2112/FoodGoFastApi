from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.roles.model import Role


def get_role_by_id(db: Session, role_id: UUID) -> Role | None:
    return db.get(Role, role_id)


def get_role_by_name(db: Session, name: str) -> Role | None:
    return db.scalars(select(Role).where(Role.name == name)).first()
