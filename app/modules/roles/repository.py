from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.roles.model import Role


def get_role_by_id(db: Session, role_id: UUID) -> Role | None:
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Role | None:
    return db.query(Role).filter(Role.name == name).first()
