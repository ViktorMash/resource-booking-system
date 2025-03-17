from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.models.model_base import BaseModel
from app.db.models.model_user import user_group


class GroupModel(BaseModel):
    __tablename__ = "groups"

    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)

    # relations to other tables
    users = relationship("UserModel", secondary=user_group, back_populates="groups")  # many-to-many
    permissions = relationship("PermissionModel", back_populates="group")  # one-to-many

    def __repr__(self):
        return f"<Group {self.name}>"