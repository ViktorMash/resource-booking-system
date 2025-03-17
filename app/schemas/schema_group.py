from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GroupBase(BaseModel):
    name: str
    description: Optional[str]


class GroupCreate(GroupBase):
    pass


class GroupSchema(GroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True