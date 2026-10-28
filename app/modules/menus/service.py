from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.modules.auth import authorization
from app.modules.auth.auth_types import TokenClaims
from app.modules.menus import repository
from app.modules.menus.model import Category, MenuItem
from app.modules.menus.schema import (
    CategoryCreate,
    CategoryUpdate,
    MenuItemCreate,
    MenuItemUpdate,
)
from app.modules.restaurants import repository as restaurant_repository
from app.modules.restaurants.model import Restaurant
from app.modules.restaurants.service import verify_restaurant_owner_or_admin


def _get_restaurant_with_access(
    db: Session, restaurant_id: UUID, current_user: TokenClaims
) -> Restaurant:
    restaurant = restaurant_repository.get_restaurant_by_id(db, restaurant_id)
    if restaurant is None:
        raise NotFoundException("Restaurant not found")

    verify_restaurant_owner_or_admin(db, restaurant, current_user)
    return restaurant


def _can_view_inactive_restaurant(
    db: Session, restaurant: Restaurant, current_user: TokenClaims | None
) -> bool:
    if current_user is None:
        return False

    caller_role = authorization.resolve_caller_role(db, current_user)

    if authorization.is_admin_role(caller_role):
        return True

    return str(restaurant.owner_id) == current_user["sub"]


# ---------------- Category Management ----------------


def create_category(
    db: Session,
    restaurant_id: UUID,
    data: CategoryCreate,
    current_user: TokenClaims,
) -> Category:
    _ = _get_restaurant_with_access(db, restaurant_id, current_user)

    existing = repository.get_category_by_name(db, restaurant_id, data.name)
    if existing is not None:
        raise ConflictException(
            "Category with this name already exists for this restaurant"
        )

    try:
        category = repository.create_category(db, restaurant_id, data)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(category)
    return category


def get_categories(
    db: Session,
    restaurant_id: UUID,
    current_user: TokenClaims | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Category]:
    restaurant = restaurant_repository.get_restaurant_by_id(db, restaurant_id)
    if restaurant is None:
        raise NotFoundException("Restaurant not found")

    if not restaurant.is_active and not _can_view_inactive_restaurant(
        db, restaurant, current_user
    ):
        raise NotFoundException("Restaurant not found")

    return repository.get_categories_by_restaurant(
        db, restaurant_id, skip=skip, limit=limit
    )


def get_category_by_id(
    db: Session,
    category_id: UUID,
    current_user: TokenClaims | None = None,
    restaurant_id: UUID | None = None,
) -> Category:
    category = repository.get_category_by_id(db, category_id)
    if category is None:
        raise NotFoundException("Category not found")

    if restaurant_id is not None and category.restaurant_id != restaurant_id:
        raise NotFoundException("Category not found")

    restaurant = restaurant_repository.get_restaurant_by_id(db, category.restaurant_id)
    if restaurant is None:
        raise NotFoundException("Restaurant not found")

    if not restaurant.is_active and not _can_view_inactive_restaurant(
        db, restaurant, current_user
    ):
        raise NotFoundException("Category not found")

    return category


def update_category(
    db: Session,
    category_id: UUID,
    data: CategoryUpdate,
    current_user: TokenClaims,
    restaurant_id: UUID | None = None,
) -> Category:
    category = repository.get_category_by_id(db, category_id)
    if category is None:
        raise NotFoundException("Category not found")

    if restaurant_id is not None and category.restaurant_id != restaurant_id:
        raise NotFoundException("Category not found")

    _ = _get_restaurant_with_access(db, category.restaurant_id, current_user)

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return category

    if data.name is not None and data.name.strip().lower() != category.name.lower():
        existing = repository.get_category_by_name(
            db, category.restaurant_id, data.name.strip()
        )
        if existing is not None and existing.id != category.id:
            raise ConflictException(
                "Category with this name already exists for this restaurant"
            )

    try:
        updated = repository.update_category(db, category, update_data)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(updated)
    return updated


def delete_category(
    db: Session,
    category_id: UUID,
    current_user: TokenClaims,
    restaurant_id: UUID | None = None,
) -> None:
    category = repository.get_category_by_id(db, category_id)
    if category is None:
        raise NotFoundException("Category not found")

    if restaurant_id is not None and category.restaurant_id != restaurant_id:
        raise NotFoundException("Category not found")

    _ = _get_restaurant_with_access(db, category.restaurant_id, current_user)

    item_count = repository.count_menu_items_in_category(db, category_id)
    if item_count > 0:
        raise ConflictException("Cannot delete category with associated menu items")

    try:
        repository.delete_category(db, category)
        db.commit()
    except Exception:
        db.rollback()
        raise


# ---------------- Menu Item Management ----------------


def create_menu_item(
    db: Session,
    restaurant_id: UUID,
    data: MenuItemCreate,
    current_user: TokenClaims,
) -> MenuItem:
    _ = _get_restaurant_with_access(db, restaurant_id, current_user)

    if data.price < 0:
        raise ValidationException("Price must be non-negative")

    if data.category_id is not None:
        category = repository.get_category_by_id(db, data.category_id)
        if category is None:
            raise NotFoundException("Category not found")
        if category.restaurant_id != restaurant_id:
            raise ValidationException("Category does not belong to this restaurant")

    try:
        menu_item = repository.create_menu_item(db, restaurant_id, data)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(menu_item)
    return menu_item


def get_menu_items(
    db: Session,
    restaurant_id: UUID,
    current_user: TokenClaims | None = None,
    category_id: UUID | None = None,
    is_available: bool | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[MenuItem]:
    restaurant = restaurant_repository.get_restaurant_by_id(db, restaurant_id)
    if restaurant is None:
        raise NotFoundException("Restaurant not found")

    is_owner_or_admin = _can_view_inactive_restaurant(db, restaurant, current_user)

    if not restaurant.is_active and not is_owner_or_admin:
        raise NotFoundException("Restaurant not found")

    # Customers and unauthenticated users can only see available items
    availability_filter = is_available if is_owner_or_admin else True

    return repository.get_menu_items_by_restaurant(
        db,
        restaurant_id=restaurant_id,
        category_id=category_id,
        is_available=availability_filter,
        skip=skip,
        limit=limit,
    )


def get_menu_item_by_id(
    db: Session,
    item_id: UUID,
    current_user: TokenClaims | None = None,
    restaurant_id: UUID | None = None,
) -> MenuItem:
    item = repository.get_menu_item_by_id(db, item_id)
    if item is None:
        raise NotFoundException("Menu item not found")

    if restaurant_id is not None and item.restaurant_id != restaurant_id:
        raise NotFoundException("Menu item not found")

    restaurant = restaurant_repository.get_restaurant_by_id(db, item.restaurant_id)
    if restaurant is None:
        raise NotFoundException("Restaurant not found")

    is_owner_or_admin = _can_view_inactive_restaurant(db, restaurant, current_user)

    if (not restaurant.is_active or not item.is_available) and not is_owner_or_admin:
        raise NotFoundException("Menu item not found")

    return item


def update_menu_item(
    db: Session,
    item_id: UUID,
    data: MenuItemUpdate,
    current_user: TokenClaims,
    restaurant_id: UUID | None = None,
) -> MenuItem:
    item = repository.get_menu_item_by_id(db, item_id)
    if item is None:
        raise NotFoundException("Menu item not found")

    if restaurant_id is not None and item.restaurant_id != restaurant_id:
        raise NotFoundException("Menu item not found")

    _ = _get_restaurant_with_access(db, item.restaurant_id, current_user)

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return item

    if data.price is not None and data.price < 0:
        raise ValidationException("Price must be non-negative")

    if data.category_id is not None:
        category = repository.get_category_by_id(db, data.category_id)
        if category is None:
            raise NotFoundException("Category not found")
        if category.restaurant_id != item.restaurant_id:
            raise ValidationException("Category does not belong to this restaurant")

    try:
        updated = repository.update_menu_item(db, item, update_data)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(updated)
    return updated


def delete_menu_item(
    db: Session,
    item_id: UUID,
    current_user: TokenClaims,
    restaurant_id: UUID | None = None,
) -> None:
    item = repository.get_menu_item_by_id(db, item_id)
    if item is None:
        raise NotFoundException("Menu item not found")

    if restaurant_id is not None and item.restaurant_id != restaurant_id:
        raise NotFoundException("Menu item not found")

    _ = _get_restaurant_with_access(db, item.restaurant_id, current_user)

    try:
        repository.delete_menu_item(db, item)
        db.commit()
    except Exception:
        db.rollback()
        raise


def set_menu_item_availability(
    db: Session,
    item_id: UUID,
    is_available: bool,
    current_user: TokenClaims,
    restaurant_id: UUID | None = None,
) -> MenuItem:
    item = repository.get_menu_item_by_id(db, item_id)
    if item is None:
        raise NotFoundException("Menu item not found")

    if restaurant_id is not None and item.restaurant_id != restaurant_id:
        raise NotFoundException("Menu item not found")

    _ = _get_restaurant_with_access(db, item.restaurant_id, current_user)

    try:
        updated = repository.update_menu_item(db, item, {"is_available": is_available})
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(updated)
    return updated
