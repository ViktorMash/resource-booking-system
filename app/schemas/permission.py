from datetime import datetime
from typing import Optional

from pydantic import BaseModel



class PermissionBase(BaseModel):
    action: str
    resource_id: int
    user_id: Optional[int]
    group_id: Optional[int]



class PermissionCreate(PermissionBase):
    pass


class PermissionSchema(PermissionBase):
    id: int

    class Config:
        from_attributes = True


# token
class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    expires_at: Optional[str]