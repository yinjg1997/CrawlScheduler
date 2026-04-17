from .crawlers import router as crawlers_router
from .tasks import router as tasks_router
from .schedules import router as schedules_router
from .websocket import router as websocket_router
from .auth import router as auth_router
from .users import router as users_router
from .projects import router as projects_router
from .dashboard import router as dashboard_router

__all__ = ["crawlers_router", "tasks_router", "schedules_router", "websocket_router", "auth_router", "users_router", "projects_router", "dashboard_router"]
