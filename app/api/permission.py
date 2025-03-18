from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query, Path, Body
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel, GroupModel, ResourceModel, PermissionModel
from app.schemas import PermissionCreate, PermissionSchema, PermissionAction
from app.core.users import get_current_superuser
from app.core.responses import ApiResponse, CustomException


router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.post("/", response_model=PermissionSchema, summary="Create new permission")
def create_permission(
        permission: PermissionCreate,
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
    """
    Create a new permission that grants a user or group access to a resource.

    Permissions define what actions (view, book, manage) users or groups can perform on resources.
    Each permission must be associated with exactly one resource and either one user or one group.

    Returns:
        PermissionSchema: The created permission
    """

    # Check if the resource exists
    resource = db.query(ResourceModel).filter(ResourceModel.id == permission.resource_id).first()
    if not resource:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Resource not found",
            details=f"Resource with ID: '{permission.resource_id}' does not exist"
        )

    # Check that either user or group is specified, but not both
    if permission.user_id and permission.group_id:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid permission assignment",
            details="Permission must be assigned to either user or group, not both"
        )

    # Check if the user exists, if a user is specified in the permission
    if permission.user_id:
        user = db.query(UserModel).filter(UserModel.id == permission.user_id).first()
        if not user:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                details=f"User with ID: '{permission.user_id}' does not exist"
            )

    # Check if the group exists, if a group is specified in the permission
    if permission.group_id:
        group = db.query(GroupModel).filter(GroupModel.id == permission.group_id).first()
        if not group:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Group not found",
                details=f"Group with ID: '{permission.group_id}' does not exist"
            )

    # Check if a similar permission already exists
    existing_permission = db.query(PermissionModel).filter(
        PermissionModel.resource_id == permission.resource_id,
        PermissionModel.action == permission.action,
        PermissionModel.user_id == permission.user_id if permission.user_id else True,
        PermissionModel.group_id == permission.group_id if permission.group_id else True
    ).first()

    if existing_permission:
        target_type = "user" if permission.user_id else "group"
        target_id = permission.user_id if permission.user_id else permission.group_id
        raise CustomException(
            status_code=status.HTTP_409_CONFLICT,
            message="Permission already exists",
            details=f"A permission for {target_type} with ID: '{target_id}' on resource '{resource.name}' with action '{permission.action}' already exists"
        )

    # create new permission
    db_permission = PermissionModel(
        action=permission.action,
        user_id=permission.user_id,
        group_id=permission.group_id,
        resource_id=permission.resource_id
    )

    # save permission
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)

    return ApiResponse.success(
        data=db_permission,
        message=f"New permission has been created for resource '{resource.name}'",
    )


@router.get("/", response_model=List[PermissionSchema], summary="Get permissions info")
def get_permissions(
        resource_id: Optional[int] = Query(None, description="Filter by resource ID"),
        user_id: Optional[int] = Query(None, description="Filter by user ID"),
        group_id: Optional[int] = Query(None, description="Filter by group ID"),
        action: Optional[PermissionAction] = Query(None, description="Filter by permission action"),
        skip: int = 0,
        limit: int = 20,
        db: Session = Depends(get_db)
):
    """
    Get list of permissions with optional filtering.

    This endpoint allows admins to retrieve and filter permission entries.
    Permissions can be filtered by resource, user, group, and/or action.

    Returns:
        List[PermissionSchema]: List of permissions matching the filter criteria
    """

    # Start with base query
    query = db.query(PermissionModel)

    # Apply filters if provided
    if resource_id:
        # Verify resource exists
        resource = db.query(ResourceModel).filter(ResourceModel.id == resource_id).first()
        if not resource:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Resource not found",
                details=f"Resource with ID:{resource_id} does not exist"
            )
        query = query.filter(PermissionModel.resource_id == resource_id)

    if user_id:
        # Verify user exists
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                details=f"User with ID:{user_id} does not exist"
            )
        query = query.filter(PermissionModel.user_id == user_id)

    if group_id:
        # Verify group exists
        group = db.query(GroupModel).filter(GroupModel.id == group_id).first()
        if not group:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Group not found",
                details=f"Group with ID:{group_id} does not exist"
            )
        query = query.filter(PermissionModel.group_id == group_id)

    if action:
        query = query.filter(PermissionModel.action == action)

    # Count total matching records before pagination
    total_count = query.count()

    # Apply pagination and get results
    permissions = query.order_by(PermissionModel.resource_id).offset(skip).limit(limit).all()

    # Build response message based on filters
    filter_parts = []
    if resource_id:
        filter_parts.append(f"resource_id={resource_id}")
    if user_id:
        filter_parts.append(f"user_id={user_id}")
    if group_id:
        filter_parts.append(f"group_id={group_id}")
    if action:
        filter_parts.append(f"action={action.name.capitalize()}")

    filter_message = ", ".join(filter_parts)
    if filter_message:
        filter_message = f" with filters: {filter_message}"

    pagination_info = f"Showing from {skip} to {limit}, ordered by 'Resource ID' ascending"

    return ApiResponse.success(
        data=permissions,
        message=f"Permissions{filter_message} loaded. {pagination_info}",
    )


@router.put("/{permission_id}", response_model=PermissionSchema, summary="Update permission")
def update_permission(
        permission_id: int = Path(..., gt=0, description="The ID of the permission to update"),
        permission_update: PermissionCreate = Body(..., description="Updated permission data"),
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
    """
    Update an existing permission.

    This endpoint allows administrators to modify the details of an existing permission,
    including changing the resource, user/group association, or permission action level.

    Returns:
        PermissionSchema: The updated permission
    """
    # Check if the permission exists
    db_permission = db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()
    if not db_permission:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Permission not found",
            details=f"Permission with ID: {permission_id} does not exist"
        )

    # Check if the resource exists
    resource = db.query(ResourceModel).filter(ResourceModel.id == permission_update.resource_id).first()
    if not resource:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Resource not found",
            details=f"Resource with ID: {permission_update.resource_id} does not exist"
        )

    # Check that either user or group is specified, but not both
    if permission_update.user_id and permission_update.group_id:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid permission assignment",
            details="Permission must be assigned to either user or group, not both"
        )

    if not permission_update.user_id and not permission_update.group_id:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Missing permission target",
            details="Permission must be assigned to either user or group"
        )

    # Validate user_id and group_id - treat 0 as invalid
    if permission_update.user_id is not None:
        if permission_update.user_id <= 0:
            raise CustomException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid user ID",
                details=f"User ID must be greater than 0, got {permission_update.user_id}"
            )
        user = db.query(UserModel).filter(UserModel.id == permission_update.user_id).first()
        if not user:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                details=f"User with ID: {permission_update.user_id} does not exist"
            )

    if permission_update.group_id is not None:
        if permission_update.group_id <= 0:
            raise CustomException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid group ID",
                details=f"Group ID must be greater than 0, got {permission_update.group_id}"
            )
        group = db.query(GroupModel).filter(GroupModel.id == permission_update.group_id).first()
        if not group:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Group not found",
                details=f"Group with ID: {permission_update.group_id} does not exist"
            )

    # Check if a duplicate permission would be created by this update
    duplicate_query = db.query(PermissionModel).filter(
        PermissionModel.id != permission_id,
        PermissionModel.resource_id == permission_update.resource_id,
        PermissionModel.action == permission_update.action
    )

    # Add user or group filter to the duplicate check query
    if permission_update.user_id:
        duplicate_query = duplicate_query.filter(PermissionModel.user_id == permission_update.user_id)
    else:
        duplicate_query = duplicate_query.filter(PermissionModel.user_id.is_(None))

    if permission_update.group_id:
        duplicate_query = duplicate_query.filter(PermissionModel.group_id == permission_update.group_id)
    else:
        duplicate_query = duplicate_query.filter(PermissionModel.group_id.is_(None))

    duplicate_check = duplicate_query.first()

    if duplicate_check:
        target_type = "user" if permission_update.user_id else "group"
        target_id = permission_update.user_id if permission_update.user_id else permission_update.group_id
        raise CustomException(
            status_code=status.HTTP_409_CONFLICT,
            message="Duplicate permission",
            details=f"A permission for {target_type} with ID: {target_id} on resource '{resource.name}' with action '{permission_update.action}' already exists"
        )

    # Update permission fields
    db_permission.action = permission_update.action
    db_permission.resource_id = permission_update.resource_id

    # Handle user_id and group_id assignment correctly
    # When updating from one type to another, make sure to set the old one to None
    if permission_update.user_id:
        db_permission.user_id = permission_update.user_id
        db_permission.group_id = None
    elif permission_update.group_id:
        db_permission.group_id = permission_update.group_id
        db_permission.user_id = None

    try:
        # Save changes
        db.commit()
        db.refresh(db_permission)
    except Exception as e:
        db.rollback()
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error",
            details=f"Failed to update permission: {str(e)}"
        )

    return ApiResponse.success(
        data=db_permission,
        message=f"Permission with ID: {permission_id} has been updated",
    )


@router.delete("/{permission_id}", status_code=status.HTTP_200_OK, summary="Delete permission")
def delete_permission(
        permission_id: int = Path(..., gt=0, description="The ID of the permission to delete"),
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
    """
    Delete an existing permission.

    This endpoint allows administrators to completely remove a permission entry.
    Once deleted, the user or group will no longer have the specified access to the resource.

    Returns:
        None: Returns success response with no data
    """

    # Check if the permission exists
    db_permission = db.query(PermissionModel).filter(PermissionModel.id == permission_id).first()
    if not db_permission:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Permission not found",
            details=f"Permission with ID: {permission_id} does not exist"
        )

    # Get details before deletion for response message
    permission_info = {
        "resource_id": db_permission.resource_id,
        "action": db_permission.action,
        "user_id": db_permission.user_id,
        "group_id": db_permission.group_id
    }

    # Try to get resource name
    resource = db.query(ResourceModel).filter(ResourceModel.id == db_permission.resource_id).first()
    resource_name = resource.name if resource else f"ID:{db_permission.resource_id}"

    # Determine target (user or group)
    target_info = ""
    if db_permission.user_id:
        user = db.query(UserModel).filter(UserModel.id == db_permission.user_id).first()
        target_info = f"user '{user.username if user else db_permission.user_id}'"
    elif db_permission.group_id:
        group = db.query(GroupModel).filter(GroupModel.id == db_permission.group_id).first()
        target_info = f"group '{group.name if group else db_permission.group_id}'"

    # Delete the permission
    db.delete(db_permission)
    db.commit()

    return ApiResponse.success(
        data=None,
        message=f"Permission with ID: {permission_id} has been deleted",
        details=f"Removed {db_permission.action} permission for {target_info} on resource '{resource_name}'",
    )