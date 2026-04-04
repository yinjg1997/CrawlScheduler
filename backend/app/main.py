from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json

from .database import engine, Base
from .config import settings
from .api import crawlers_router, tasks_router, schedules_router, websocket_router, python_environments_router
from .scheduler.scheduler import setup_scheduler, shutdown_scheduler


class TimezoneAwareJSONResponse(JSONResponse):
    """Custom JSON response that adds timezone info to datetime objects"""

    def render(self, content) -> bytes:
        def default(obj):
            if isinstance(obj, datetime):
                # If datetime is naive, assume it's UTC and convert to target timezone
                if obj.tzinfo is None:
                    obj = obj.replace(tzinfo=timezone.utc)
                # Convert to configured timezone (East 8)
                return obj.astimezone(ZoneInfo(settings.TIMEZONE)).isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=default
        ).encode("utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Setup scheduler
    if settings.SCHEDULER_ENABLED:
        await setup_scheduler()

    print("CrawlScheduler started successfully!")

    yield

    # Shutdown
    if settings.SCHEDULER_ENABLED:
        await shutdown_scheduler()
    print("CrawlScheduler shutdown complete!")


app = FastAPI(
    title="CrawlScheduler",
    description="Crawler Task Scheduling Platform",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=TimezoneAwareJSONResponse
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(crawlers_router)
app.include_router(tasks_router)
app.include_router(schedules_router)
app.include_router(websocket_router)
app.include_router(python_environments_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "CrawlScheduler",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
