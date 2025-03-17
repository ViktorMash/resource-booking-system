from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class BookingBase(BaseModel):
    resource_id: int
    start_time: datetime
    end_time: datetime

    @model_validator(mode='after')
    def validate_dates(self) -> 'BookingBase':
        if self.start_time >= self.end_time:
            raise ValueError('end_time must be after start_time')
        return self


class BookingCreate(BookingBase):
    pass


class BookingSchema(BookingBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class BookingInfo(BaseModel):
    id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    status: str

    class Config:
        from_attributes = True