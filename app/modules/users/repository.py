from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.model import User
from app.modules.users.schema import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def get_user_by_id(db: Session, user_id: str | UUID) -> User | None:
    if isinstance(user_id, str):
        try:
            user_id = UUID(user_id)
        except ValueError:
            return None

    return db.get(User, user_id)


def signup(db: Session, user_data: UserCreate, hashed_password: str) -> User:
    user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        phone=user_data.phone,
        role_id=user_data.role_id,
        is_active=True,
    )

    db.add(user)
    db.flush()

    return user


def update_user(db: Session, user: User, update_data: dict[str, object]) -> User:
    for field, value in update_data.items():
        setattr(user, field, value)

    db.flush()

    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.flush()


def get_all_users(db: Session) -> list[User]:
    return list(db.scalars(select(User)).all())
