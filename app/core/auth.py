from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from app.core import settings

# password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Oauth2 setup to obtain tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/login")


def get_password_hash(*, password) -> str:
    """ generate password hash """
    return pwd_context.hash(password)


def verify_password(*, plain_password, hashed_password) -> bool:
    """ check stored hash with password """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, data: dict, expires_delta: Optional[timedelta] = None) -> dict[str, str]:
    """
     create JWT token for user
    :param data: dict data for the token
    :param expires_delta: (optional) token lifetime, min
    """

    to_encode = data.copy()  # to keep original data
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ACCESS_TOKEN_ALGORITHM)

    return {
        "token_type": "bearer",
        "access_token": encoded_jwt,
        "expires_at": expire.strftime(settings.DATETIME_TEMPLATE),
    }