from datetime import datetime
from typing import Optional, List
from .booking import BookingConflict

from pydantic import BaseModel, Field, model_validator



class ResourceBase(BaseModel):
    name: str= Field(..., min_length=3, max_length=30, description="Resource name")
    description: Optional[str] = Field(None, max_length=100, description="Resource description")
    capacity: int = Field(default=1, gt=0, description="Resource capacity")


class ResourceCreate(ResourceBase):
    pass


class ResourceAvailabilityRequest(BaseModel):
    resource_id: Optional[int] = None
    resource_name: Optional[str] = None
    start_time: datetime
    end_time: datetime

    @model_validator(mode='after')
    def validate_dates(self) -> 'ResourceAvailabilityRequest':
        if self.start_time >= self.end_time:
            raise ValueError('end_time must be after start_time')
        return self


class ResourceAvailabilityResponse(BaseModel):
    is_available: bool
    message: Optional[str]
    resource_id: int
    resource_name: str
    capacity: int
    available_capacity: int
    conflicting_bookings: List[BookingConflict] = Field(default_factory=list)


class ResourceSchema(ResourceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

