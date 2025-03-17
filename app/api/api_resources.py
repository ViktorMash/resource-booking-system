from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel, ResourceModel, BookingModel
from app.schemas import ResourceCreate, ResourceSchema, ResourceAvailabilityResponse, ResourceAvailabilityRequest
from app.core.users import get_current_active_user, check_permissions


router = APIRouter(prefix="/resources", tags=["resources"])


@router.post("/", response_model=ResourceSchema)
def create_resource(
        resource: ResourceCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # check if the user is superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail=f"Not enough permissions for user '{current_user.email}'")

    # check if the resource with this name already exists
    db_resource = db.query(ResourceModel).filter(ResourceModel.name == resource.name).first()
    if db_resource:
        raise HTTPException(status_code=400, detail=f"Resource '{resource.name}' already exists")

    db_resource = ResourceModel(
        name=resource.name,
        description=resource.description,
        capacity=resource.capacity
    )

    # save resource
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)

    return db_resource


@router.get("/", response_model=List[ResourceSchema])
def get_resources(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # get resources with pagination
    resources = db.query(ResourceModel).offset(skip).limit(limit).all()
    return resources


@router.post("/availability", response_model=ResourceAvailabilityResponse)
def check_resource_availability(
        request: ResourceAvailabilityRequest,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    Check the availability of a resource for a specified time period.

    This is an additional endpoint that extends the API functionality by providing
    a specialized way to check resource availability before attempting to book it.
    Users can verify resource availability for a desired period without creating a booking

    Returns:
        ResourceAvailabilityResponse: Detailed information about resource availability
    """
    resource = None

    if request.resource_id:
        resource = db.query(ResourceModel).filter(ResourceModel.id == request.resource_id).first()
    if request.resource_name:
        resource = db.query(ResourceModel).filter(ResourceModel.name == request.resource_name).first()

    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource not found or request doesn't contain either id or name")

    # Check permission to view resource
    if not check_permissions(db, current_user, request.resource_id, action="view"):
        raise HTTPException(
            status_code=403,
            detail=f"Not enough permissions to view resource '{resource.name}'"
        )

    # Find all bookings in the requested period
    conflicting_bookings = db.query(BookingModel).filter(
        BookingModel.resource_id == request.resource_id,
        BookingModel.status.in_(["pending", "approved"]),
        BookingModel.start_time < request.end_time,
        BookingModel.end_time > request.start_time
    ).all()

    # calculate capacity
    available_capacity = max(0, resource.capacity - len(conflicting_bookings))
    is_available = available_capacity >= 0

    # prepare response
    message = None
    if not is_available:
        message = f"Resource '{request.resource_name}' is fully booked during the requested time"

    return ResourceAvailabilityResponse(
        is_available=is_available,
        resource_name=str(resource.name),
        capacity=int(str(resource.capacity)),
        available_capacity=available_capacity,
        conflicting_bookings=conflicting_bookings if current_user.is_superuser else list(),
        message=message
    )
