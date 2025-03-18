from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import func, desc, or_, and_
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel, ResourceModel, BookingModel
from app.core.users import get_current_superuser, get_current_user, check_permissions
from app.core.responses import ApiResponse, CustomException
from app.schemas import (
    ResourceCreate, ResourceSchema, ResourceAvailabilityResponse, ResourceAvailabilityRequest,
    PermissionAction,
    BookingStatus, BookingConflict
)


router = APIRouter(prefix="/resources", tags=["resources"])


@router.post("/", response_model=ResourceSchema, summary="Create new resource")
def create_resource(
        resource: ResourceCreate,
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
    # check if the resource with this name already exists
    db_resource = db.query(ResourceModel).filter(
        func.lower(ResourceModel.name) == resource.name.lower()
    ).first()
    if db_resource:
        raise CustomException(
            status_code=status.HTTP_409_CONFLICT,
            message="Duplicate resource name",
            details=f"Resource '{db_resource.name}' already exists"
        )

    db_resource = ResourceModel(
        name=resource.name,
        description=resource.description,
        capacity=resource.capacity
    )

    # save resource
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)

    return ApiResponse.success(
        data=db_resource,
        message="New resource has been added to database",
    )


@router.get("/", response_model=List[ResourceSchema], summary="Get resources info")
def get_resources(
        resource_id: Optional[int] = Query(None, description="Filter by resource ID"),
        skip: int = 0,
        limit: int = 20,
        db: Session = Depends(get_db)
):
    if resource_id:
        group = db.query(ResourceModel).filter(ResourceModel.id == resource_id).first()
        if not group:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Resource with ID:{resource_id} is not exists in database"
            )
        return ApiResponse.success(
        data=group,
        message=f"Resource with ID:{resource_id} has been loaded from database",
    )

    # return list of users with pagination
    return ApiResponse.success(
        data=db.query(ResourceModel).order_by(desc(ResourceModel.capacity)).offset(skip).limit(limit).all(),
        message=f"Resources info has been loaded from DB. " \
                f"Pagination from {skip} to {limit}, ordered by 'capacity' descending",
    )


@router.post("/availability", response_model=ResourceAvailabilityResponse, summary="Check resources availability")
def check_resource_availability(
        request: ResourceAvailabilityRequest,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Check the availability of a resource for a specified time period.

    This endpoint provides a way to check resource availability before booking.
    The response indicates whether the resource is available and, for admin users,
    provides minimal information about conflicting bookings if any exist.

    Returns:
        ResourceAvailabilityResponse: Concise information about resource availability
    """

    # Find resource by ID or name
    if request.resource_id:
        resource = db.query(ResourceModel).filter(ResourceModel.id == request.resource_id).first()
        if not resource:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Resource with ID:{request.resource_id} not found"
            )
    elif request.resource_name:
        resource = db.query(ResourceModel).filter(
            func.lower(ResourceModel.name) == request.resource_name.lower()
        ).first()
        if not resource:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Resource with name '{request.resource_name}' not found"
            )
    else:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Either resource_id or resource_name must be provided"
        )

    # Check permission to view resource
    if not check_permissions(db, current_user, resource.id, action=PermissionAction.VIEW):
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Not enough permissions to view this resource"
        )

    # Find all bookings in the requested period
    conflicting_bookings_query = db.query(BookingModel).filter(
        BookingModel.resource_id == resource.id,
        BookingModel.booking_status.in_([BookingStatus.PENDING.value, BookingStatus.APPROVED.value]),
        or_(
            # New booking starts during an existing booking
            and_(
                BookingModel.start_time <= request.start_time,
                BookingModel.end_time > request.start_time
            ),
            # New booking ends during an existing booking
            and_(
                BookingModel.start_time < request.end_time,
                BookingModel.end_time >= request.end_time
            ),
            # New booking completely contains an existing booking
            and_(
                BookingModel.start_time >= request.start_time,
                BookingModel.end_time <= request.end_time
            ),
            # Existing booking completely contains the new booking
            and_(
                BookingModel.start_time <= request.start_time,
                BookingModel.end_time >= request.end_time
            )
        )
    )

    # Count conflicting bookings first (more efficient than fetching all records)
    conflicting_count = conflicting_bookings_query.count()
    available_capacity = resource.capacity - conflicting_count
    is_available = available_capacity > 0

    # Only get booking details if superuser AND there are conflicts
    booking_info_list = []
    if current_user.is_superuser and conflicting_count > 0:
        conflicting_bookings = conflicting_bookings_query.all()
        for booking in conflicting_bookings:
            booking_dict = {
                "booking_status": booking.booking_status,
                "start_time": booking.start_time,
                "end_time": booking.end_time
            }
            booking_info_list.append(BookingConflict.model_validate(booking_dict))

    # Simple, concise message based on availability
    if not is_available:
        message = f"Resource '{resource.name}' is unavailable for requested time"
    else:
        message = f"Resource '{resource.name}' has capacity for booking"

    return ApiResponse.success(
        data=ResourceAvailabilityResponse(
            is_available=is_available,
            message=message,
            resource_id=resource.id,
            resource_name=resource.name,
            capacity=resource.capacity,
            available_capacity=max(0, available_capacity),
            conflicting_bookings=booking_info_list
        ),
        message=f"Availability checked for '{resource.name}'"
    )
