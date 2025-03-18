from typing import List, Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel, GroupModel
from app.schemas import GroupCreate, GroupSchema
from app.core.users import get_current_superuser
from app.core.responses import ApiResponse, CustomException


router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/", response_model=GroupSchema, summary="Create new group")
def create_group(
        group: GroupCreate,
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
    # check if the group with this name already exists
    db_group = db.query(GroupModel).filter(
        func.lower(GroupModel.name) == group.name.lower()
    ).first()
    if db_group:
        raise CustomException(
            status_code=status.HTTP_409_CONFLICT,
            message="Duplicate group name",
            details=f"Group '{db_group.name}' already exists"
        )

    db_group = GroupModel(
        name=group.name,
        description=group.description
    )

    # save group
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    return ApiResponse.success(
        data=db_group,
        message="New group has been added to database",
    )


@router.get("/", response_model=List[GroupSchema], summary="Get groups info")
def get_users(
        group_id: Optional[int] = Query(None, description="Filter by group ID"),
        skip: int = 0,
        limit: int = 20,
        db: Session = Depends(get_db),
        _: UserModel = Depends(get_current_superuser)
):
    if group_id:
        group = db.query(GroupModel).filter(GroupModel.id == group_id).first()
        if not group:
            raise CustomException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Group with ID:{group_id} is not exists in database"
            )
        return ApiResponse.success(
        data=group,
        message=f"Group with ID:{group_id} has been loaded from database",
    )

    # return list of users with pagination
    return ApiResponse.success(
        data=db.query(GroupModel).order_by(GroupModel.name).offset(skip).limit(limit).all(),
        message=f"Groups info has been loaded from DB. " \
                f"Pagination from {skip} to {limit}, ordered by 'name' ascending",
    )
