from fastapi import APIRouter

router = APIRouter(tags=["base"])


@router.get("/")
def read_root():
    return {"message": "Welcome to Resource Booking System API", "docs": "/docs"}
