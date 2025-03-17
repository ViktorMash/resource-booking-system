from sqlalchemy import Column, String, Boolean, Table, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.models.model_base import BaseModel
from app.core import settings

# Relational table between users and groups (many-to-many), this table doesn't have its own model
user_group = Table(
    "user_group",
    BaseModel.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True)
)


class UserModel(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=settings.DEFAULT_USER_ACTIVE)
    is_superuser = Column(Boolean, default=settings.DEFAULT_USER_SUPERUSER)

    # relations to other tables
    groups = relationship("GroupModel", secondary=user_group, back_populates="users")  # many-to-many
    permissions = relationship("PermissionModel", back_populates="user")  # one-to-many
    bookings = relationship("BookingModel", back_populates="user")  # one-to-many

    def __repr__(self):
        return f"<User {self.username}>"