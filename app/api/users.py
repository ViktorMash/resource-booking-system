from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel
from app.schemas import UserCreate, UserSchema
from app.core.users import get_current_user, get_current_superuser, create_user
from app.core.responses import ApiResponse, CustomException


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema, summary="Create new user")
def create_new_user(
        user: UserCreate,
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
    # check if the user with this email already exists
    db_user = db.query(UserModel).filter(
        func.lower(UserModel.email) == user.email
    ).first()
    if db_user:
        raise CustomException(
            status_code=status.HTTP_409_CONFLICT,
            message="Duplicate email",
            details=f"Email '{user.email}' already registered"
        )

    # check if the user with this username already exists
    db_user = db.query(UserModel).filter(
        func.lower(UserModel.username) == user.username.lower()
    ).first()
    if db_user:
        raise CustomException(
            status_code=status.HTTP_409_CONFLICT,
            message="Duplicate username",
            details=f"Username '{user.username}' already registered"
        )

    # create and save user
    db_user = create_user(user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return ApiResponse.success(
        data=db_user,
        message="New user has been added to database",
    )


@router.get("/", response_model=List[UserSchema], summary="Get users info")
def get_users(
        user_id: Optional[int] = Query(None, description="Filter by user ID"),
        skip: int = 0,
        limit: int = 20,
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
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
                f"Pagination from {skip} to {limit}, ordered by 'email' ascending",
    )


@router.get("/me/", response_model=UserSchema, summary="Get current user info")
def get_user_me(
        current_user: UserModel = Depends(get_current_user)
):
    return ApiResponse.success(
        data=current_user,
        message="Current user data has been loaded from DB",
    )