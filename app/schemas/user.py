from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr



class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = True


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str]


class UserSchema(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
