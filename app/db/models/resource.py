from sqlalchemy import Column, String, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class ResourceModel(BaseModel):
    __tablename__ = "resources"

    name = Column(String(30), unique=True, nullable=False)
    description = Column(String(100), nullable=True)
    capacity = Column(Integer, default=1)
    schedule = Column(JSON, nullable=True)

    # relations to other tables
    permissions = relationship("PermissionModel", back_populates="resource")  # one-to-many
    bookings = relationship("BookingModel", back_populates="resource")  # one-to-many

    def __repr__(self):
        return f"<Resource {self.name}>"