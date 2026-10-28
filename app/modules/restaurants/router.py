from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.auth_types import TokenClaims
from app.modules.auth.dependencies import (
    get_current_user,
    get_optional_current_user,
    require_restaurant_creator,
)
from app.modules.restaurants import service as restaurant_service
from app.modules.restaurants.model import Restaurant
from app.modules.restaurants.schema import (
    RestaurantCreate,
    RestaurantResponse,
    RestaurantStatusUpdate,
    RestaurantUpdate,
)

router = APIRouter(prefix="/api/restaurants", tags=["Restaurants"])

DBSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[TokenClaims, Depends(get_current_user)]
RestaurantCreator = Annotated[TokenClaims, Depends(require_restaurant_creator)]
OptionalCurrentUser = Annotated[TokenClaims | None, Depends(get_optional_current_user)]
SkipQuery = Annotated[int, Query(ge=0)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
IsActiveQuery = Annotated[bool | None, Query()]


@router.post(
    "/create-restaurant",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create restaurant",
)
def create_restaurant(
    data: RestaurantCreate,
    db: DBSession,
    current_user: RestaurantCreator,
) -> Restaurant:
    return restaurant_service.create_restaurant(db, data, current_user)


@router.get(
    "/get-all-restaurants",
    response_model=list[RestaurantResponse],
    summary="Get all restaurants",
)
def get_restaurants(
    db: DBSession,
    current_user: OptionalCurrentUser = None,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
    is_active: IsActiveQuery = None,
) -> list[Restaurant]:
    return restaurant_service.get_restaurants(
        db, current_user=current_user, skip=skip, limit=limit, is_active=is_active
    )


@router.get("/my-restaurants", response_model=list[RestaurantResponse])
@router.get("/mine", response_model=list[RestaurantResponse])
def get_my_restaurants(
    db: DBSession,
    current_user: CurrentUser,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
) -> list[Restaurant]:
    return restaurant_service.get_my_restaurants(
        db, current_user=current_user, skip=skip, limit=limit
    )


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant_by_id(
    restaurant_id: UUID,
    db: DBSession,
    current_user: OptionalCurrentUser = None,
) -> Restaurant:
    return restaurant_service.get_restaurant_by_id(
        db, restaurant_id, current_user=current_user
    )


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: UUID,
    data: RestaurantUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> Restaurant:
    return restaurant_service.update_restaurant(db, restaurant_id, data, current_user)


@router.delete(
    "/{restaurant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_restaurant(
    restaurant_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    restaurant_service.delete_restaurant(db, restaurant_id, current_user)


@router.patch("/{restaurant_id}/activate", response_model=RestaurantResponse)
@router.put("/{restaurant_id}/activate", response_model=RestaurantResponse)
def activate_restaurant(
    restaurant_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> Restaurant:
    return restaurant_service.set_restaurant_status(
        db, restaurant_id, is_active=True, current_user=current_user
    )


@router.patch("/{restaurant_id}/deactivate", response_model=RestaurantResponse)
@router.put("/{restaurant_id}/deactivate", response_model=RestaurantResponse)
def deactivate_restaurant(
    restaurant_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> Restaurant:
    return restaurant_service.set_restaurant_status(
        db, restaurant_id, is_active=False, current_user=current_user
    )


@router.patch("/{restaurant_id}/status", response_model=RestaurantResponse)
def set_restaurant_status(
    restaurant_id: UUID,
    data: RestaurantStatusUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> Restaurant:
    return restaurant_service.set_restaurant_status(
        db, restaurant_id, is_active=data.is_active, current_user=current_user
    )
