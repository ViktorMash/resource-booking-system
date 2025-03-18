from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GroupBase(BaseModel):
    name: str= Field(..., min_length=3, max_length=30, description="Group name")
    description: Optional[str] = Field(None, max_length=100, description="Group description")


class GroupCreate(GroupBase):
    pass


class GroupSchema(GroupBase):
    id: int = Field(gt=0)
    created_at: datetime

    class Config:
        from_attributes = True