import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    # argon2 has no length limit, the cap just stops someone posting a 10 MB "password"
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
