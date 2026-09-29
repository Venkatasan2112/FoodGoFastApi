from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None
    role_id: UUID | None = None


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(extra="forbid")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
