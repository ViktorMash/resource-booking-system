import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path

# Go 3 levels up from app/core/config.py and set path to .env in the docker folder
dotenv_path = Path(__file__).resolve().parent.parent.parent  / "docker" / ".env"

# load env variables from .env file
load_dotenv(dotenv_path)

# load env variables into settings
class Settings(BaseSettings):
    # app base settings
    PROJECT_NAME: str = "Resource Booking System"
    VERSION: str = "1.0"
    DESCRIPTION: str = "A web application for booking various resources (computational resources, meeting rooms, equipment, etc.) with user permissions management"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", False)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")


    # DB settings
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "rbs")
    DB_SERVER: str = os.getenv("DB_SERVER", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")

    # SQLAlchemy URI
    @property
    def sqlalchemy_db_uri(self) -> str:
        return f'postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}/{self.DB_NAME}'

    SQLALCHEMY_ECHO: bool = True  # show verbose DB queries in console
    SQLALCHEMY_POOL_SIZE: int = 5  # number of DB connections
    SQLALCHEMY_POOL_MAX_OVERFLOW: int = 5  # additional DB connections

    # JWT tokens
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ACCESS_TOKEN_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True
    )

settings = Settings()