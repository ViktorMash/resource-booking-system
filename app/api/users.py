from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel
from app.schemas import UserCreate, UserSchema
from app.core.auth import get_current_active_user, get_password_hash


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema)
def create_user(
        user: UserCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # check if the user is superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail=f"Not enough permissions for user '{current_user.email}'")

    # check if the user with this email already exists
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail=f"Email '{current_user.email}' already registered")

    # check if the user with this username already exists
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail=f"Username '{current_user.username}' already registered")

    # create user with hashed password
    hashed_password = get_password_hash(password=user.password)
    db_user = UserModel(
        email=str(user.email),
        username=user.username,
        hashed_password=hashed_password,
        is_active=user.is_active,
        is_superuser=user.is_superuser
    )

    # save user
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/", response_model=List[UserSchema])
def get_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # check if the user is superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail=f"Not enough permissions for user '{current_user.email}'")

    # get list of users with pagination
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users


@router.get("/me/", response_model=UserSchema)
def get_user_me(
        current_user: UserModel = Depends(get_current_active_user)
):
    return current_user