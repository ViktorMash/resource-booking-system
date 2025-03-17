from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel, GroupModel, ResourceModel, PermissionModel
from app.schemas import PermissionCreate, PermissionSchema
from app.core.users import get_current_active_user


router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.post("/", response_model=PermissionSchema)
def create_permission(
        permission: PermissionCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # check if the user is superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail=f"Not enough permissions for user '{current_user.email}'")

    # check if the resource exists
    resource = db.query(ResourceModel).filter(ResourceModel.id == permission.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # check if the user exists, in case if a user is in the permission
    if permission.user_id:
        user = db.query(UserModel).filter(UserModel.id == permission.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID='{permission.user_id}' not found")

    # check if the group exists, in case if a group in the permission
    if permission.group_id:
        group = db.query(GroupModel).filter(GroupModel.id == permission.group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group '{permission.group_id}' not found")

    # check that either user or group is presented in permission
    if permission.user_id and permission.group_id:
        raise HTTPException(status_code=400, detail="Permission must be assigned to either user or group, not both")

    if not permission.user_id and not permission.group_id:
        raise HTTPException(status_code=400, detail="Permission must be assigned to either user or group")

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

    return db_permission