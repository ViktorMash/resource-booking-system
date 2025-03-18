from datetime import datetime
from typing import Optional
import re

from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core import settings


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email")
    username: str= Field(..., min_length=3, max_length=30, description="Login user name")
    is_active: Optional[bool] = Field(settings.DEFAULT_USER_ACTIVE, description="Is user active")
    is_superuser: Optional[bool] = Field(settings.DEFAULT_USER_SUPERUSER, description="Is user admin")

    @field_validator('username')
    def username_must_be_alphanumeric(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError('Username must be between 3 and 50 characters, and contain only letters, numbers, underscores, and hyphens')
        return v

    @classmethod
    def validate_password(cls, v):
        if (len(v) < 8 or
           not any(char.isdigit() for char in v) or
           not any(char in '!@#$%^&*()-_=+[]{}|;:,.<>?/' for char in v)
        ):
            raise ValueError('Password must be at least 8 characters long, contain at least one digit and one special character')

        common_passwords = ['password123!', 'admin123!', 'qwerty123!', '12345', 'qazwsx']
        if v.lower() in common_passwords:
            raise ValueError('This password is too common and easily guessable')

        return v


class UserCreate(UserBase):
    password: str = Field(..., description="Login user password")

    @field_validator('password')
    def password_must_be_strong(cls, v):
        return cls.validate_password(v)


class SuperUserCreate(UserBase):
    is_active: bool = Field(True, description="Admin always active")
    is_superuser: bool = Field(True, description="Admin flag")
    password: str = Field(..., description="Admin password")

    @field_validator('password')
    def password_must_be_strong(cls, v):
        return cls.validate_password(v)

    @field_validator('is_superuser')
    def must_be_superuser(cls, v):
        if not v:
            raise ValueError('Initial user must have is_superuser=True')
        return v


class UserUpdate(UserBase):
    email: Optional[EmailStr] = Field(None, description="User new email")
    username: Optional[str] = Field(None, min_length=3, max_length=30, description="User new name")
    password: Optional[str] = Field(None, description="User new password")


    @field_validator('password')
    def password_must_be_strong(cls, v):
        return cls.validate_password(v)

class UserSchema(UserBase):
    id: int = Field(..., gt=0, description="User unique ID")
    created_at: datetime = Field(..., description="User creation date and time")

    class Config:
        from_attributes = True
