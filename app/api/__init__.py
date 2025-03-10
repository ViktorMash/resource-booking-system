from fastapi import APIRouter

#from .base import router as base_router
from .auth import router as auth_router
from .users import router as users_router
from .groups import router as group_router
from .permission import router as permission_router
from .bookings import router as booking_router
from .resources import router as resources_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(group_router)
router.include_router(permission_router)
router.include_router(booking_router)
router.include_router(resources_router)
