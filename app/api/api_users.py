from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel
from app.schemas import UserCreate, UserSchema
from app.core.users import get_current_active_user, create_user
from app.core.responses import ApiResponse, CustomException


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema, summary="Create new user")
def create_user(
        user: UserCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # check if the user is superuser
    if not current_user.is_superuser:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Not enough permissions",
            details=f"Not enough permissions for user '{current_user.email}'"
        )

    # check if the user with this email already exists
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Duplicate email",
            details=f"Email '{current_user.email}' already registered"
        )

    # check if the user with this username already exists
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Duplicate username",
            details=f"Username '{current_user.username}' already registered"
        )

    # create and save user
    db_user = create_user(user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return ApiResponse.success(
        data=db_user,
        message="New user added",
    )


@router.get("/", response_model=List[UserSchema], summary="Get users info")
def get_users(
        user_id: Optional[int] = Query(None, description="Filter by user ID"),
        skip: int = 0,
        limit: int = 20,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # check if the user is superuser
    if not current_user.is_superuser:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Not enough permissions",
            details=f"Not enough permissions for user '{current_user.email}'"
        )
    if user_id:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"User with ID:{user_id} is not exists in database"
            )
        return ApiResponse.success(
        data=user,
        message=f"User with ID:{user_id} has been loaded from database",
    )

    # return list of users with pagination
    return ApiResponse.success(
        data=db.query(UserModel).order_by(UserModel.email).offset(skip).limit(limit).all(),
        message=f"Users info has been loaded from DB. " \
                f"Pagination from {skip} to {limit}, ordered by user email ascending",
    )


@router.get("/me/", response_model=UserSchema, summary="Get current user info")
def get_user_me(
        current_user: UserModel = Depends(get_current_active_user)
):
    return ApiResponse.success(
        data=current_user,
        message="Current user data has been loaded from DB",
    )