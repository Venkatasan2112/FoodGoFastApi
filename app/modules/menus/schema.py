from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None

    model_config = ConfigDict(extra="forbid")


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None

    model_config = ConfigDict(extra="forbid")


class CategoryResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    price: Decimal = Field(..., ge=Decimal(0), decimal_places=2)
    category_id: UUID | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_available: bool = True

    model_config = ConfigDict(extra="forbid")


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=Decimal(0), decimal_places=2)
    category_id: UUID | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_available: bool | None = None

    model_config = ConfigDict(extra="forbid")


class MenuItemAvailabilityUpdate(BaseModel):
    is_available: bool

    model_config = ConfigDict(extra="forbid")


class MenuItemResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    category_id: UUID | None = None
    name: str
    description: str | None = None
    price: Decimal
    image_url: str | None = None
    is_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
