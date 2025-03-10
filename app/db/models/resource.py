from sqlalchemy import Column, String, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class ResourceModel(BaseModel):
    __tablename__ = "resources"

    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    capacity = Column(Integer, default=1)
    schedule = Column(JSON, nullable=True)

    # relations to other tables
    permissions = relationship("PermissionModel", back_populates="resource")  # one-to-many
    bookings = relationship("BookingModel", back_populates="resource")  # one-to-many

    def __repr__(self):
        return f"<Resource {self.name}>"


class BookingModel(BaseModel):
    __tablename__ = "bookings"

    # foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)

    # booking time
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # booking status
    status = Column(String, default="pending")  # pending, approved, rejected, cancelled

    # relations to other tables
    user = relationship("UserModel")
    resource = relationship("ResourceModel", back_populates="bookings")

    def __repr__(self):
        return f"<Booking {self.resource.name} by {self.user.username}>"