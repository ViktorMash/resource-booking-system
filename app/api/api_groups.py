from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import UserModel, GroupModel
from app.schemas import GroupCreate, GroupSchema
from app.core.users import get_current_active_user


router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/", response_model=GroupSchema)
def create_group(
        group: GroupCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # check if the user is superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail=f"Not enough permissions for user '{current_user.email}'")

    # check if the group with this name already exists
    db_group = db.query(GroupModel).filter(GroupModel.name == group.name).first()
    if db_group:
        raise HTTPException(status_code=400, detail=f"Group '{group.name}' already exists")

    db_group = GroupModel(
        name=group.name,
        description=group.description
    )

    # save group
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    return db_group