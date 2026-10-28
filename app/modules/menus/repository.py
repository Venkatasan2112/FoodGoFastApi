from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.menus.model import Category, MenuItem
from app.modules.menus.schema import CategoryCreate, MenuItemCreate


def create_category(db: Session, restaurant_id: UUID, data: CategoryCreate) -> Category:
    category = Category(
        restaurant_id=restaurant_id,
        name=data.name,
        description=data.description,
    )
    db.add(category)
    db.flush()
    return category


def get_category_by_id(db: Session, category_id: UUID) -> Category | None:
    return db.get(Category, category_id)


def get_category_by_name(
    db: Session, restaurant_id: UUID, name: str
) -> Category | None:
    return db.scalars(
        select(Category).where(
            Category.restaurant_id == restaurant_id,
            func.lower(Category.name) == name.strip().lower(),
        )
    ).first()


def get_categories_by_restaurant(
    db: Session, restaurant_id: UUID, skip: int = 0, limit: int = 100
) -> list[Category]:
    return list(
        db.scalars(
            select(Category)
            .where(Category.restaurant_id == restaurant_id)
            .order_by(Category.name.asc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


def update_category(
    db: Session, category: Category, update_data: dict[str, object]
) -> Category:
    for field, value in update_data.items():
        setattr(category, field, value)

    db.flush()
    return category


def delete_category(db: Session, category: Category) -> None:
    db.delete(category)
    db.flush()


def count_menu_items_in_category(db: Session, category_id: UUID) -> int:
    result = db.scalar(
        select(func.count(MenuItem.id)).where(MenuItem.category_id == category_id)
    )
    return result or 0


def create_menu_item(
    db: Session, restaurant_id: UUID, data: MenuItemCreate
) -> MenuItem:
    menu_item = MenuItem(
        restaurant_id=restaurant_id,
        category_id=data.category_id,
        name=data.name,
        description=data.description,
        price=data.price,
        image_url=data.image_url,
        is_available=data.is_available,
    )
    db.add(menu_item)
    db.flush()
    return menu_item


def get_menu_item_by_id(db: Session, item_id: UUID) -> MenuItem | None:
    return db.get(MenuItem, item_id)


def get_menu_items_by_restaurant(
    db: Session,
    restaurant_id: UUID,
    category_id: UUID | None = None,
    is_available: bool | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[MenuItem]:
    query = select(MenuItem).where(MenuItem.restaurant_id == restaurant_id)

    if category_id is not None:
        query = query.where(MenuItem.category_id == category_id)

    if is_available is not None:
        query = query.where(MenuItem.is_available == is_available)

    query = query.order_by(MenuItem.created_at.asc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def update_menu_item(
    db: Session, item: MenuItem, update_data: dict[str, object]
) -> MenuItem:
    for field, value in update_data.items():
        setattr(item, field, value)

    db.flush()
    return item


def delete_menu_item(db: Session, item: MenuItem) -> None:
    db.delete(item)
    db.flush()
