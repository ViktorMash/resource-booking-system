from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class BookingModel(BaseModel):
    __tablename__ = "bookings"

    # foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)

    # booking time
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # booking status
    booking_status = Column(String(30), default="pending")  # pending, approved, rejected, cancelled

    # relations to other tables
    user = relationship("UserModel")
    resource = relationship("ResourceModel", back_populates="bookings")

    def __repr__(self):
        return f"<Booking {self.resource.name} by {self.user.username}>"