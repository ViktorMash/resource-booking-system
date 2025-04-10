from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.models.base import BaseModel


class PermissionModel(BaseModel):
    __tablename__ = "permissions"

    action = Column(String(20), nullable=False)  # action for user - view, book, manage
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)

    # relations to other tables
    user = relationship("UserModel", back_populates="permissions")
    group = relationship("GroupModel", back_populates="permissions")
    resource = relationship("ResourceModel", back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.action} on {self.resource.name}>"