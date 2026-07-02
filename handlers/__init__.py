from .start import router as start_router
from .schedule import router as schedule_router
from .profile import router as profile_router
from .homework import router as homework_router
from .admin import router as admin_router

__all__ = [
    "start_router",
    "schedule_router",
    "profile_router",
    "homework_router",
    "admin_router",
]
