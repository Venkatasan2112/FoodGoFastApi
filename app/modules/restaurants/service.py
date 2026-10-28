from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException
from app.modules.auth import authorization
from app.modules.auth.auth_types import TokenClaims
from app.modules.restaurants import repository
from app.modules.restaurants.model import Restaurant
from app.modules.restaurants.schema import RestaurantCreate, RestaurantUpdate


def verify_restaurant_owner_or_admin(
    db: Session, restaurant: Restaurant, current_user: TokenClaims
) -> None:
    caller_role = authorization.resolve_caller_role(db, current_user)

    if authorization.is_admin_role(caller_role):
        return

    if str(restaurant.owner_id) == current_user[
        "sub"
    ] and authorization.can_manage_restaurants(caller_role):
        return

    raise AuthorizationException("Not authorized to modify this restaurant")


def create_restaurant(
    db: Session, data: RestaurantCreate, current_user: TokenClaims
) -> Restaurant:
    caller_role = authorization.resolve_caller_role(db, current_user)

    if not authorization.can_manage_restaurants(caller_role):
        raise AuthorizationException("Not authorized to create restaurants")

    try:
        owner_id = UUID(current_user["sub"])
    except (ValueError, TypeError):
        raise AuthorizationException("Invalid user ID format")

    try:
        restaurant = repository.create_restaurant(db, data, owner_id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(restaurant)
    return restaurant


def get_restaurants(
    db: Session,
    current_user: TokenClaims | None = None,
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
) -> list[Restaurant]:
    if current_user is None:
        return repository.get_restaurants(db, skip=skip, limit=limit, is_active=True)

    caller_role = authorization.resolve_caller_role(db, current_user)

    if authorization.is_admin_role(caller_role):
        return repository.get_restaurants(
            db, skip=skip, limit=limit, is_active=is_active
        )

    if authorization.is_owner_role(caller_role):
        try:
            owner_id = UUID(current_user["sub"])
        except (ValueError, TypeError):
            raise AuthorizationException("Invalid user ID format")
        return repository.get_restaurants(
            db, skip=skip, limit=limit, owner_id=owner_id, is_active=is_active
        )

    # Regular USER / Customer: Browse active restaurants only
    return repository.get_restaurants(db, skip=skip, limit=limit, is_active=True)


def get_my_restaurants(
    db: Session,
    current_user: TokenClaims,
    skip: int = 0,
    limit: int = 100,
) -> list[Restaurant]:
    caller_role = authorization.resolve_caller_role(db, current_user)

    if not authorization.can_manage_restaurants(caller_role):
        raise AuthorizationException("Restaurant owner or admin access required")

    try:
        owner_id = UUID(current_user["sub"])
    except (ValueError, TypeError):
        raise AuthorizationException("Invalid user ID format")

    return repository.get_restaurants(db, skip=skip, limit=limit, owner_id=owner_id)


def can_view_inactive_restaurant(
    db: Session, restaurant: Restaurant, current_user: TokenClaims | None
) -> bool:
    if current_user is None:
        return False

    caller_role = authorization.resolve_caller_role(db, current_user)

    if authorization.is_admin_role(caller_role):
        return True

    return (
        str(restaurant.owner_id) == current_user["sub"]
        and authorization.can_manage_restaurants(caller_role)
    )


def get_restaurant_by_id(
    db: Session,
    restaurant_id: UUID,
    current_user: TokenClaims | None = None,
) -> Restaurant:
    restaurant = repository.get_restaurant_by_id(db, restaurant_id)
    if restaurant is None:
        raise NotFoundException("Restaurant not found")

    if restaurant.is_active:
        return restaurant

    if not can_view_inactive_restaurant(db, restaurant, current_user):
        raise NotFoundException("Restaurant not found")

    return restaurant


def update_restaurant(
    db: Session,
    restaurant_id: UUID,
    data: RestaurantUpdate,
    current_user: TokenClaims,
) -> Restaurant:
    restaurant = repository.get_restaurant_by_id(db, restaurant_id)
    if restaurant is None:
        raise NotFoundException("Restaurant not found")

    verify_restaurant_owner_or_admin(db, restaurant, current_user)

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return restaurant

    try:
        updated_restaurant = repository.update_restaurant(db, restaurant, update_data)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(updated_restaurant)
    return updated_restaurant


def delete_restaurant(
    db: Session,
    restaurant_id: UUID,
    current_user: TokenClaims,
) -> None:
    restaurant = repository.get_restaurant_by_id(db, restaurant_id)
    if restaurant is None:
        raise NotFoundException("Restaurant not found")

    verify_restaurant_owner_or_admin(db, restaurant, current_user)

    try:
        repository.delete_restaurant(db, restaurant)
        db.commit()
    except Exception:
        db.rollback()
        raise


def set_restaurant_status(
    db: Session,
    restaurant_id: UUID,
    is_active: bool,
    current_user: TokenClaims,
) -> Restaurant:
    restaurant = repository.get_restaurant_by_id(db, restaurant_id)
    if restaurant is None:
        raise NotFoundException("Restaurant not found")

    verify_restaurant_owner_or_admin(db, restaurant, current_user)

    try:
        updated = repository.update_restaurant(db, restaurant, {"is_active": is_active})
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(updated)
    return updated
