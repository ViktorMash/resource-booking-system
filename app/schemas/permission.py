from enum import Enum
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


class PermissionAction(str, Enum):
    VIEW = "view"
    BOOK = "book"
    MANAGE = "manage"


class PermissionBase(BaseModel):
    action: PermissionAction = Field(default=PermissionAction.VIEW)
    resource_id: int = Field(gt=0)
    user_id: Optional[int] = Field(default=None, description="If permission for user")
    group_id: Optional[int] = Field(default=None, description="If permission for group")



class PermissionCreate(PermissionBase):
    pass


class PermissionSchema(PermissionBase):
    id: int = Field(gt=0)

    class Config:
        from_attributes = True


# token
class TokenSchema(BaseModel):
    token_type: str
    access_token: str
    expires_at: Optional[str]