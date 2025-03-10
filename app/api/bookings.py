from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel, ResourceModel, BookingModel
from app.schemas import BookingCreate, BookingSchema
from app.core.auth import get_current_active_user, check_permission, check_resource_availability


router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingSchema)
def create_booking(
        booking: BookingCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # check if a resource exists. Blocks resource while updating (adds SQL operator FOR UPDATE)
    resource = db.query(ResourceModel).filter(ResourceModel.id == booking.resource_id).with_for_update().first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource with ID: {booking.resource_id} not found")

    # check if a user has a permission to book a resource
    if not check_permission(db, current_user, booking.resource_id, action="book"):
        raise HTTPException(status_code=403, detail=f"Not enough permissions for user '{current_user.email}' to book resource '{resource.name}'")

    # check if a resource is available in requesting time
    is_available, reason = check_resource_availability(
        db,
        booking.resource_id,
        booking.start_time,
        booking.end_time
    )

    if not is_available:
        raise HTTPException(status_code=400, detail=reason)

    # create new booking
    db_booking = BookingModel(
        user_id=current_user.id,
        resource_id=booking.resource_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status="pending"  # initial status
    )

    # save booking
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return db_booking


@router.get("/", response_model=List[BookingSchema])
def get_bookings(
        skip: int = 0,
        limit: int = 100,
        resource_id: Optional[int] = None,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    get all bookings with ability to filter by resource
    common users get their bookings, superusers get all bookings
    """
    query = db.query(BookingModel)

    # filter by user if not superuser
    if not current_user.is_superuser:
        query = query.filter(BookingModel.user_id == current_user.id)

    # filter by resource if provided
    if resource_id:
        query = query.filter(BookingModel.resource_id == resource_id)

    # apply pagination
    bookings = query.offset(skip).limit(limit).all()

    return bookings


@router.put("/{booking_id}", response_model=BookingSchema)
def update_booking(
        booking_id: int,
        booking_update: BookingCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    update current booking
    common users can update only their bookings, superusers can update any booking
    """
    # check if the booking exists
    db_booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail=f"Booking with ID: {booking_id} not found")

    # check permissions
    if not current_user.is_superuser and db_booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail=f"Not enough permissions for user '{current_user.email}'"
        )

    # check if resource exists
    resource = db.query(ResourceModel).filter(ResourceModel.id == booking_update.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource not found")

    # check if user has permission to book a resource
    if db_booking.resource_id != booking_update.resource_id:
        if not check_permission(db, current_user, booking_update.resource_id, action="book"):
            raise HTTPException(
                status_code=403,
                detail=f"Not enough permissions for user '{current_user.email}'"
            )

    # check if a resource is available
    is_available, reason = check_resource_availability(
        db,
        booking_update.resource_id,
        booking_update.start_time,
        booking_update.end_time,
        booking_id=booking_id  # exclude current booking in order to avoid conflict with self
    )

    if not is_available:
        raise HTTPException(status_code=400, detail=reason)

    # refresh booking
    db_booking.resource_id = booking_update.resource_id
    db_booking.start_time = booking_update.start_time
    db_booking.end_time = booking_update.end_time

    db.commit()
    db.refresh(db_booking)

    return db_booking


@router.delete("/{booking_id}", response_model=BookingSchema)
def cancel_booking(
        booking_id: int,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    cancel booking (set status == 'cancelled')
    common users can cancel only their bookings, superusers can cancel any booking
    """
    # check if the booking exists
    db_booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail=f"Booking with ID: {booking_id} not found")

    # check permissions
    if not current_user.is_superuser and db_booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail=f"Not enough permissions for user '{current_user.email}'"
        )
    db_booking.status = "cancelled"
    db.commit()

    return {"message": f"Booking {booking_id} has been cancelled successfully"}
