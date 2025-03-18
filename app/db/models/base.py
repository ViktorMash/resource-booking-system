from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase  # base class for models, converts python to SQL

from app.core import settings

# SQLAlchemy base model with common fields for all tables
class BaseModel(DeclarativeBase):
    __abstract__ = True  # a table won't be created from this class

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now())

    @hybrid_property
    def created_at_formatted(self):
        if self.created_at:
            return self.created_at.strftime(settings.DATE_FORMAT)
        return None

    @hybrid_property
    def updated_at_formatted(self):
        if self.updated_at:
            return self.updated_at.strftime(settings.DATE_FORMAT)
        return None