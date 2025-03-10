from datetime import datetime
from typing import Optional, List
from .booking import BookingInfo

from pydantic import BaseModel, Field, model_validator



class ResourceBase(BaseModel):
    name: str
    description: Optional[str]
    capacity: int = 1


class ResourceCreate(ResourceBase):
    pass


class ResourceAvailabilityRequest(BaseModel):
    resource_id: Optional[int]
    resource_name: Optional[str]
    start_time: datetime
    end_time: datetime

    @model_validator(mode='after')
    def validate_dates(self) -> 'ResourceAvailabilityRequest':
        if self.start_time >= self.end_time:
            raise ValueError('end_time must be after start_time')
        return self


class ResourceAvailabilityResponse(BaseModel):
    is_available: bool
    resource_name: str
    capacity: int
    available_capacity: int
    conflicting_bookings: List[BookingInfo] = Field(default_factory=list)
    message: Optional[str]


class ResourceSchema(ResourceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

