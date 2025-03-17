from fastapi import APIRouter

from .api_auth import router as auth_router
from .api_users import router as users_router
from .api_groups import router as group_router
from .api_permission import router as permission_router
from .api_bookings import router as booking_router
from .api_resources import router as resources_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(group_router)
router.include_router(permission_router)
router.include_router(booking_router)
router.include_router(resources_router)
