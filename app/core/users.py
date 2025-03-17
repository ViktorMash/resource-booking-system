from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core import settings
from app.db import get_db
from app.db.models import UserModel, ResourceModel, PermissionModel, BookingModel
from app.schemas import UserCreate, SuperUserCreate
from .auth import get_password_hash, verify_password, oauth2_scheme


def create_user(user: UserCreate | SuperUserCreate) -> UserModel:
    """ create user with hashed password """

    return UserModel(
        email=str(user.email),
        username=user.username,
        hashed_password=get_password_hash(password=user.password),
        is_active= user.is_active,
        is_superuser=user.is_superuser
    )


def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    """ get user data by email """
    return db.query(UserModel).filter(UserModel.email == email).first()


def authenticate_user(db: Session, *, email: str, password: str) -> Optional[UserModel]:
    """ auth user by email and password """

    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(plain_password=password, hashed_password=user.hashed_password):
        return None
    return user


def get_current_user(db: Session = Depends(get_db), *, token: str = Depends(oauth2_scheme)) -> UserModel:
    """ get current authenticated user from token """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ACCESS_TOKEN_ALGORITHM])
        email: str = payload.get("sub")  # token is created with the field "sub" that contains email
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # get user from database
    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """ check if authenticated user is active """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



def check_permissions(db: Session, user: UserModel, resource_id: int, *, action: str) -> bool:
    """ check if user has permission to get resource
        this checks both direct user permissions and permissions granted via groups
    """

    if user.is_superuser:
        return True

    user_permission = db.query(PermissionModel).filter(
        PermissionModel.user_id == user.id,
        PermissionModel.resource_id == resource_id,
        PermissionModel.action == action
    ).first()

    if user_permission:
        return True

    group_permission = db.query(PermissionModel).filter(
        PermissionModel.group_id.in_([g.id for g in user.groups]),
        PermissionModel.resource_id == resource_id,
        PermissionModel.action == action
    ).first()

    if group_permission:
        return True

    return False


def check_resource_availability(
        db: Session,
        resource_id: int,
        start_time: datetime,
        end_time: datetime,
        booking_id: Optional[int] = None
) -> tuple[bool, Optional[str]]:
    """
    checks if a resource is available for booking during the specified period
    :params: booking_id: Optional, if provided, will be excluded from the check (for updates)
    :return: tuple of ("is available": bool, "reason if not available": str | None)
    """

    # get the resource
    resource = db.query(ResourceModel).filter(ResourceModel.id == resource_id).first()
    if not resource:
        return False, "Resource not found"

    # get all bookings for this time period
    query = db.query(BookingModel).filter(
        BookingModel.resource_id == resource.id,
        BookingModel.status.in_(["pending", "approved"]),
        BookingModel.start_time < end_time,
        BookingModel.end_time > start_time,
    )

    # exclude the current booking for updates
    if booking_id:
        query = query.filter(BookingModel.id != booking_id)

    conflicting_booking = query.all()

    if conflicting_booking:
        # if the resource capacity == 1, any conflicts means the resource is not available
        if resource.capacity == 1:
            booking = conflicting_booking[0]
            return False, f"Resource {resource.name} is already booked from {booking.start_time} till {booking.end_time}"

    # for resources with higher capacity, check if we have reached the limit
    if resource.capacity > 1:
        booked_count = len(conflicting_booking)
        if booked_count >= resource.capacity:
            return False, f"Resource {resource.name} is fully booked for the requested time"

    return True, None
