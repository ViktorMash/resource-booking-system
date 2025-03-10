from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase  # base class for models, converts python to SQL

# SQLAlchemy base model with common fields for all tables
class BaseModel(DeclarativeBase):
    __abstract__ = True  # a table won't be created from this class

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
