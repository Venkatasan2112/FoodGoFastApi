from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    address: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    is_active: bool = True

    model_config = ConfigDict(extra="forbid")


class RestaurantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    address: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")


class RestaurantStatusUpdate(BaseModel):
    is_active: bool

    model_config = ConfigDict(extra="forbid")


class RestaurantResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    address: str
    phone: str | None = None
    owner_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
