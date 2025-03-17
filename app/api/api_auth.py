from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import TokenSchema, UserSchema, SuperUserCreate
from app.db.models import UserModel
from app.core.auth import create_access_token
from app.core.users import authenticate_user, create_user
from app.core.responses import ApiResponse, CustomException


router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenSchema, summary="Login for access token")
def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    Login with existing user to get session token
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise CustomException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Authorization error",
            details="Incorrect username or password",
        )
    token_data = create_access_token(data={"sub": user.email})

    return ApiResponse.success(
        data=token_data,
        message="Successful login",
    )


@router.post("/initial-setup", response_model=UserSchema, summary="Create admin user while setting up the system")
def create_initial_admin(
        user: SuperUserCreate,
        db: Session = Depends(get_db)
):
    """
    Creates the initial admin user if no users exist in the database.
    This endpoint is only available when the table "users" in the database is empty.
    """
    # Check if any users exist
    get_all_users = db.query(UserModel).exists()
    has_users = db.query(get_all_users).scalar()

    if has_users:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Initial setup already completed",
            details="Cannot create another initial admin"
        )

    # create and save admin user
    db_user = create_user(user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return ApiResponse.success(
        data=db_user,
        message="Superuser added for initial setup",
    )