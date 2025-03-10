from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# interface for DB connection
engine = create_engine(
    settings.sqlalchemy_db_uri,
    echo=settings.SQLALCHEMY_ECHO,
    #pool_size=settings.SQLALCHEMY_POOL_SIZE,
    #max_overflow=settings.SQLALCHEMY_POOL_MAX_OVERFLOW,
)

Session = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """ Create and close DB session for every single query """
    db = Session()
    try:
        yield db
    finally:
        db.close()
