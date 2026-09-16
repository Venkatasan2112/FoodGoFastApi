from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None
    role_id: UUID


class UserProfileUpdate(BaseModel):
    name: str
    phone: str | None = None


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str | None
    role_id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
