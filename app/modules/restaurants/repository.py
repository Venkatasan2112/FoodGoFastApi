from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.restaurants.model import Restaurant
from app.modules.restaurants.schema import RestaurantCreate


def create_restaurant(
    db: Session, data: RestaurantCreate, owner_id: UUID
) -> Restaurant:
    restaurant = Restaurant(
        name=data.name,
        description=data.description,
        address=data.address,
        phone=data.phone,
        owner_id=owner_id,
        is_active=data.is_active,
    )
    db.add(restaurant)
    db.flush()
    return restaurant


def get_restaurant_by_id(db: Session, restaurant_id: UUID) -> Restaurant | None:
    return db.get(Restaurant, restaurant_id)


def get_restaurants(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    owner_id: UUID | None = None,
    is_active: bool | None = None,
) -> list[Restaurant]:
    query = select(Restaurant)

    if owner_id is not None:
        query = query.where(Restaurant.owner_id == owner_id)

    if is_active is not None:
        query = query.where(Restaurant.is_active == is_active)

    query = query.order_by(Restaurant.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def update_restaurant(
    db: Session, restaurant: Restaurant, update_data: dict[str, object]
) -> Restaurant:
    for field, value in update_data.items():
        setattr(restaurant, field, value)

    db.flush()
    return restaurant


def delete_restaurant(db: Session, restaurant: Restaurant) -> None:
    db.delete(restaurant)
    db.flush()
