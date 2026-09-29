from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None
    role_id: UUID


class UpdateUserRequest(BaseModel):
    name: str | None = None
    phone: str | None = None

    model_config = ConfigDict(extra="forbid")


class UserProfileResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str | None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str | None
    role_id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
