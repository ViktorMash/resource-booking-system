from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, model_validator, Field


class BookingStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class BookingTime(BaseModel):
    start_time: datetime
    end_time: datetime

    @model_validator(mode='after')
    def validate_dates(self) -> 'BookingTime':
        if self.start_time >= self.end_time:
            raise ValueError('end_time must be after start_time')
        return self


class BookingConflict(BookingTime):
    booking_status: BookingStatus = Field(default=BookingStatus.PENDING)


class BookingCreate(BookingTime):
    resource_id: int = Field(gt=0)


class BookingBase(BaseModel):
    id: int = Field(gt=0)
    resource_id: int
    resource_name: Optional[str] = None
    user_id: int = Field(gt=0)
    booking_status: BookingStatus = Field(default=BookingStatus.PENDING)


class BookingSchema(BookingBase, BookingTime):
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
