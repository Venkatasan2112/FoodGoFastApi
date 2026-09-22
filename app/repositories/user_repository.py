from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str | UUID) -> User | None:
    if isinstance(user_id, str):
        try:
            user_id = UUID(user_id)
        except ValueError:
            return None

    return db.query(User).filter(User.id == user_id).first()


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

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user


def update_user(db: Session, user: User, update_data: dict[str, object]) -> User:
    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user


def delete_user(db: Session, user: User) -> None:
    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_all_users(db: Session) -> list[User]:
    return db.query(User).all()
