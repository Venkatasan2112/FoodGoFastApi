from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.dependencies import (
    get_current_user,
    get_optional_current_user,
)
from app.modules.menus import service as menu_service
from app.modules.menus.model import Category, MenuItem
from app.modules.menus.schema import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    MenuItemAvailabilityUpdate,
    MenuItemCreate,
    MenuItemResponse,
    MenuItemUpdate,
)

router = APIRouter(tags=["Menus"])

DBSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[TokenClaims, Depends(get_current_user)]
OptionalCurrentUser = Annotated[TokenClaims | None, Depends(get_optional_current_user)]
SkipQuery = Annotated[int, Query(ge=0)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
CategoryIdQuery = Annotated[UUID | None, Query()]
IsAvailableQuery = Annotated[bool | None, Query()]


@router.post(
    "/api/restaurants/{restaurant_id}/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    restaurant_id: UUID,
    data: CategoryCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> Category:
    return menu_service.create_category(
        db, restaurant_id, data, current_user=current_user
    )


@router.get(
    "/api/restaurants/{restaurant_id}/categories",
    response_model=list[CategoryResponse],
)
def get_categories(
    restaurant_id: UUID,
    db: DBSession,
    current_user: OptionalCurrentUser = None,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
) -> list[Category]:
    return menu_service.get_categories(
        db,
        restaurant_id=restaurant_id,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/api/restaurants/{restaurant_id}/categories/{category_id}",
    response_model=CategoryResponse,
)
@router.get("/api/categories/{category_id}", response_model=CategoryResponse)
def get_category_by_id(
    category_id: UUID,
    db: DBSession,
    restaurant_id: UUID | None = None,
    current_user: OptionalCurrentUser = None,
) -> Category:
    return menu_service.get_category_by_id(
        db,
        category_id=category_id,
        current_user=current_user,
        restaurant_id=restaurant_id,
    )


@router.put(
    "/api/restaurants/{restaurant_id}/categories/{category_id}",
    response_model=CategoryResponse,
)
@router.put("/api/categories/{category_id}", response_model=CategoryResponse)
@router.patch(
    "/api/restaurants/{restaurant_id}/categories/{category_id}",
    response_model=CategoryResponse,
)
@router.patch("/api/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: DBSession,
    current_user: CurrentUser,
    restaurant_id: UUID | None = None,
) -> Category:
    return menu_service.update_category(
        db,
        category_id=category_id,
        data=data,
        current_user=current_user,
        restaurant_id=restaurant_id,
    )


@router.delete(
    "/api/restaurants/{restaurant_id}/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@router.delete(
    "/api/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    restaurant_id: UUID | None = None,
) -> None:
    menu_service.delete_category(
        db,
        category_id=category_id,
        current_user=current_user,
        restaurant_id=restaurant_id,
    )


# ============================================================================
# Menu Item Endpoints
# ============================================================================


@router.post(
    "/api/restaurants/{restaurant_id}/menu-items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/api/restaurants/{restaurant_id}/items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_item(
    restaurant_id: UUID,
    data: MenuItemCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> MenuItem:
    return menu_service.create_menu_item(
        db, restaurant_id=restaurant_id, data=data, current_user=current_user
    )


@router.get(
    "/api/restaurants/{restaurant_id}/menu-items",
    response_model=list[MenuItemResponse],
)
@router.get(
    "/api/restaurants/{restaurant_id}/items",
    response_model=list[MenuItemResponse],
)
def get_menu_items(
    restaurant_id: UUID,
    db: DBSession,
    current_user: OptionalCurrentUser = None,
    category_id: CategoryIdQuery = None,
    is_available: IsAvailableQuery = None,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
) -> list[MenuItem]:
    return menu_service.get_menu_items(
        db,
        restaurant_id=restaurant_id,
        current_user=current_user,
        category_id=category_id,
        is_available=is_available,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/api/restaurants/{restaurant_id}/menu-items/{item_id}",
    response_model=MenuItemResponse,
)
@router.get(
    "/api/restaurants/{restaurant_id}/items/{item_id}",
    response_model=MenuItemResponse,
)
@router.get("/api/menu-items/{item_id}", response_model=MenuItemResponse)
def get_menu_item_by_id(
    item_id: UUID,
    db: DBSession,
    restaurant_id: UUID | None = None,
    current_user: OptionalCurrentUser = None,
) -> MenuItem:
    return menu_service.get_menu_item_by_id(
        db,
        item_id=item_id,
        current_user=current_user,
        restaurant_id=restaurant_id,
    )


@router.put(
    "/api/restaurants/{restaurant_id}/menu-items/{item_id}",
    response_model=MenuItemResponse,
)
@router.put(
    "/api/restaurants/{restaurant_id}/items/{item_id}",
    response_model=MenuItemResponse,
)
@router.put("/api/menu-items/{item_id}", response_model=MenuItemResponse)
@router.patch(
    "/api/restaurants/{restaurant_id}/menu-items/{item_id}",
    response_model=MenuItemResponse,
)
@router.patch(
    "/api/restaurants/{restaurant_id}/items/{item_id}",
    response_model=MenuItemResponse,
)
@router.patch("/api/menu-items/{item_id}", response_model=MenuItemResponse)
def update_menu_item(
    item_id: UUID,
    data: MenuItemUpdate,
    db: DBSession,
    current_user: CurrentUser,
    restaurant_id: UUID | None = None,
) -> MenuItem:
    return menu_service.update_menu_item(
        db,
        item_id=item_id,
        data=data,
        current_user=current_user,
        restaurant_id=restaurant_id,
    )


@router.delete(
    "/api/restaurants/{restaurant_id}/menu-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@router.delete(
    "/api/restaurants/{restaurant_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@router.delete(
    "/api/menu-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_menu_item(
    item_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    restaurant_id: UUID | None = None,
) -> None:
    menu_service.delete_menu_item(
        db,
        item_id=item_id,
        current_user=current_user,
        restaurant_id=restaurant_id,
    )


@router.patch(
    "/api/restaurants/{restaurant_id}/menu-items/{item_id}/availability",
    response_model=MenuItemResponse,
)
@router.patch(
    "/api/menu-items/{item_id}/availability",
    response_model=MenuItemResponse,
)
def set_menu_item_availability(
    item_id: UUID,
    data: MenuItemAvailabilityUpdate,
    db: DBSession,
    current_user: CurrentUser,
    restaurant_id: UUID | None = None,
) -> MenuItem:
    return menu_service.set_menu_item_availability(
        db,
        item_id=item_id,
        is_available=data.is_available,
        current_user=current_user,
        restaurant_id=restaurant_id,
    )


@router.patch(
    "/api/menu-items/{item_id}/available",
    response_model=MenuItemResponse,
)
def mark_menu_item_available(
    item_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> MenuItem:
    return menu_service.set_menu_item_availability(
        db,
        item_id=item_id,
        is_available=True,
        current_user=current_user,
    )


@router.patch(
    "/api/menu-items/{item_id}/unavailable",
    response_model=MenuItemResponse,
)
def mark_menu_item_unavailable(
    item_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> MenuItem:
    return menu_service.set_menu_item_availability(
        db,
        item_id=item_id,
        is_available=False,
        current_user=current_user,
    )
