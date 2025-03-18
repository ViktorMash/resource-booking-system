from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query, Path, Body
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel, ResourceModel, BookingModel
from app.schemas import BookingCreate, BookingSchema, BookingStatus, PermissionAction
from app.core.users import get_current_user, get_current_superuser, check_resource_availability, check_permissions
from app.core.responses import ApiResponse, CustomException

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingSchema, summary="Create new booking")
def create_booking(
        booking: BookingCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new booking for a resource.

    Users can book resources for which they have booking permissions.
    The system will check resource availability before creating the booking.

    Returns:
        BookingSchema: The created booking
    """
    # Check if a resource exists. Blocks resource while updating (adds SQL operator FOR UPDATE)
    resource = db.query(ResourceModel).filter(ResourceModel.id == booking.resource_id).with_for_update().first()
    if not resource:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Resource not found",
            details=f"Resource with ID: {booking.resource_id} not found"
        )

    # Check if a user has a permission to book a resource
    if not check_permissions(db, current_user, booking.resource_id, action=PermissionAction.BOOK):
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Not enough permissions",
            details=f"Not enough permissions for user '{current_user.email}' to book resource '{resource.name}'"
        )

    # Check if a resource is available in requesting time
    is_available, reason = check_resource_availability(
        db,
        booking.resource_id,
        booking.start_time,
        booking.end_time
    )

    if not is_available:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Resource unavailable",
            details=reason
        )

    # Create new booking
    db_booking = BookingModel(
        user_id=current_user.id,
        resource_id=booking.resource_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        booking_status=BookingStatus.PENDING  # Initial status
    )

    try:
        # Save booking
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
    except Exception as e:
        db.rollback()
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error",
            details=f"Failed to create booking: {str(e)}"
        )

    return ApiResponse.success(
        data=db_booking,
        message=f"Booking for resource '{resource.name}' has been created",
    )


@router.get("/", response_model=List[BookingSchema], summary="Get bookings")
def get_bookings(
        resource_id: Optional[int] = Query(None, description="Filter by resource ID"),
        booking_status: Optional[BookingStatus] = Query(None, description="Filter by booking status"),
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_superuser)
):
    """
    Get list of bookings with optional filtering.

    Regular users can only see their own bookings.
    Superusers can see all bookings in the system.
    Bookings can be filtered by resource ID and status.

    Returns:
        List[BookingSchema]: List of bookings matching the filter criteria
    """
    # Start with base query
    query = db.query(BookingModel)

    # Filter by user if not superuser
    if not current_user.is_superuser:
        query = query.filter(BookingModel.user_id == current_user.id)

    # Apply filters if provided
    if resource_id:
        # Verify resource exists
        resource = db.query(ResourceModel).filter(ResourceModel.id == resource_id).first()
        if not resource:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Resource not found",
                details=f"Resource with ID: {resource_id} does not exist"
            )
        query = query.filter(BookingModel.resource_id == resource_id)

    if booking_status:
        query = query.filter(BookingModel.booking_status == booking_status)

    # Count total matching records before pagination
    total_count = query.count()

    # Apply ordering and pagination
    bookings = query.order_by(BookingModel.start_time.desc()).offset(skip).limit(limit).all()

    # Build response message based on filters
    filter_parts = []
    if resource_id:
        filter_parts.append(f"resource_id={resource_id}")
    if booking_status:
        filter_parts.append(f"booking_status={booking_status}")

    filter_message = ", ".join(filter_parts)
    if filter_message:
        filter_message = f" with filters: {filter_message}"

    pagination_info = f"Showing {len(bookings)} of {total_count} records, from {skip} to {skip + limit}, ordered by 'Start Time' descending"

    return ApiResponse.success(
        data=bookings,
        message=f"Bookings{filter_message} loaded. {pagination_info}",
    )


@router.put("/{booking_id}", response_model=BookingSchema, summary="Update booking")
def update_booking(
        booking_id: int = Path(..., gt=0, description="The ID of the booking to update"),
        booking_update: BookingCreate = Body(..., description="Updated booking data"),
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
    """
    Update an existing booking.

    Only superuser can update bookings
    When updating a booking, the system will check resource availability

    Returns:
        BookingSchema: The updated booking
    """
    # Check if the booking exists
    db_booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not db_booking:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Booking not found",
            details=f"Booking with ID: {booking_id} does not exist"
        )
    '''
    # Check permissions - regular users can only update their own bookings
    if db_booking.user_id != current_user.id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Not enough permissions",
            details=f"User '{current_user.email}' cannot modify booking #{booking_id} owned by another user"
        )
    '''

    # Check if the booking is not in a final state
    if db_booking.booking_status in [BookingStatus.CANCELLED, BookingStatus.REJECTED]:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid booking state",
            details=f"Cannot update booking that is in '{db_booking.booking_status}' state"
        )

    # Check if resource exists
    resource = db.query(ResourceModel).filter(ResourceModel.id == booking_update.resource_id).first()
    if not resource:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Resource not found",
            details=f"Resource with ID: {booking_update.resource_id} does not exist"
        )
    '''
    # If changing resource, check booking permissions for the new resource
    if db_booking.resource_id != booking_update.resource_id:
        if not check_permissions(db, current_user, booking_update.resource_id, action="book"):
            raise CustomException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                details=f"User '{current_user.email}' does not have permission to book resource '{resource.name}'"
            )
    '''

    # Check if a resource is available for the new time period
    is_available, reason = check_resource_availability(
        db,
        booking_update.resource_id,
        booking_update.start_time,
        booking_update.end_time,
        booking_id=booking_id  # Exclude current booking to avoid conflict with self
    )

    if not is_available:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Resource unavailable",
            details=reason
        )

    # Store old resource info for message
    old_resource_id = db_booking.resource_id
    old_resource = db.query(ResourceModel).filter(ResourceModel.id == old_resource_id).first()
    old_resource_name = old_resource.name if old_resource else f"ID:{old_resource_id}"

    try:
        # Update booking
        db_booking.resource_id = booking_update.resource_id
        db_booking.start_time = booking_update.start_time
        db_booking.end_time = booking_update.end_time

        # Reset booking_status to pending if the booking details changed substantially
        if (db_booking.resource_id != old_resource_id or
                db_booking.start_time != booking_update.start_time or
                db_booking.end_time != booking_update.end_time):
            db_booking.booking_status = BookingStatus.PENDING

        db.commit()
        db.refresh(db_booking)
    except Exception as e:
        db.rollback()
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error",
            details=f"Failed to update booking: {str(e)}"
        )

    # Build detailed message
    details = "Booking updated: "
    change_parts = []

    if old_resource_id != booking_update.resource_id:
        change_parts.append(f"resource changed from '{old_resource_name}' to '{resource.name}'")

    change_parts.append(
        f"time period: {booking_update.start_time.isoformat()} to {booking_update.end_time.isoformat()}")

    details += ", ".join(change_parts)

    return ApiResponse.success(
        data=db_booking,
        message=f"Booking with ID: {booking_id} has been updated",
        details=details
    )


@router.delete("/{booking_id}", status_code=status.HTTP_200_OK, summary="Cancel booking")
def cancel_booking(
        booking_id: int = Path(..., gt=0, description="The ID of the booking to cancel"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Cancel an existing booking.

    This endpoint marks a booking as cancelled. It does not delete the booking record.
    Users can cancel only their own bookings, while superusers can cancel any booking.

    Returns:
        None: Returns success response with no data
    """
    # Check if the booking exists
    db_booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not db_booking:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Booking not found",
            details=f"Booking with ID: {booking_id} does not exist"
        )

    # Check permissions - regular users can only cancel their own bookings
    if db_booking.user_id != current_user.id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Not enough permissions",
            details=f"User '{current_user.email}' cannot cancel booking #{booking_id} owned by another user"
        )

    # Check if the booking can be cancelled
    if db_booking.booking_status in [BookingStatus.CANCELLED, BookingStatus.REJECTED]:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid booking state",
            details=f"Booking is already in '{db_booking.booking_status}' state"
        )

    # Get resource info for response message
    resource = db.query(ResourceModel).filter(ResourceModel.id == db_booking.resource_id).first()
    resource_name = resource.name if resource else f"ID:{db_booking.resource_id}"

    try:
        # Update booking status
        db_booking.booking_status = BookingStatus.CANCELLED
        db.commit()
    except Exception as e:
        db.rollback()
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error",
            details=f"Failed to cancel booking: {str(e)}"
        )

    return ApiResponse.success(
        data=None,
        message=f"Booking with ID: {booking_id} has been cancelled",
        details=f"Cancelled booking for resource '{resource_name}' from {db_booking.start_time.isoformat()} to {db_booking.end_time.isoformat()}"
    )


@router.put("/{booking_id}/status", response_model=BookingSchema, summary="Update booking status")
def update_booking_status(
        booking_id: int = Path(..., gt=0, description="The ID of the booking to update"),
        booking_status: BookingStatus = Query(..., description="New booking status"),
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
    """
    Update the status of an existing booking.

    This endpoint allows administrators to approve or reject booking requests.
    Only superusers can change booking status to approved or rejected.

    Returns:
        BookingSchema: The updated booking with new status
    """

    # Check if the booking exists
    db_booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    if not db_booking:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Booking not found",
            details=f"Booking with ID: {booking_id} does not exist"
        )

    # Check if status change is valid
    if db_booking.booking_status == booking_status:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="No status change",
            details=f"Booking is already in '{booking_status}' state"
        )

    # Some state transitions might not be allowed
    if db_booking.booking_status in [BookingStatus.CANCELLED] and booking_status != BookingStatus.PENDING:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid status transition",
            details=f"Cannot change status from '{db_booking.booking_status}' to '{booking_status}'"
        )

    # If approving, check for conflicts again to be safe
    if booking_status == BookingStatus.APPROVED:
        is_available, reason = check_resource_availability(
            db,
            int(str(db_booking.resource_id)),
            db_booking.start_time,
            db_booking.end_time,
            booking_id=booking_id
        )

        if not is_available:
            raise CustomException(
                status_code=status.HTTP_409_CONFLICT,
                message="Resource unavailable",
                details=f"Cannot approve booking due to conflict: {reason}"
            )

    # Get resource info for response message
    resource = db.query(ResourceModel).filter(ResourceModel.id == db_booking.resource_id).first()
    resource_name = resource.name if resource else f"ID:{db_booking.resource_id}"

    # Get user info for response message
    user = db.query(UserModel).filter(UserModel.id == db_booking.user_id).first()
    user_info = user.username if user else f"ID:{db_booking.user_id}"

    try:
        # Update booking status
        old_status = db_booking.booking_status
        db_booking.booking_status = booking_status
        db.commit()
        db.refresh(db_booking)
    except Exception as e:
        db.rollback()
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error",
            details=f"Failed to update booking status: {str(e)}"
        )

    return ApiResponse.success(
        data=db_booking,
        message=f"Booking status updated from '{old_status}' to '{booking_status}'",
        details=f"Updated status for booking #{booking_id} by {user_info} for resource '{resource_name}'"
    )