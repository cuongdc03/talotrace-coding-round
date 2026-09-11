"""FastAPI application entrypoint for AI Chemistry Video Request Service."""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.health import health_check
from app.api.v1.router import api_router
from app.core.config import settings
from app.repositories.sqlite_job_repository import SQLiteJobRepository
from app.services.video_service import VideoService
from app.services.worker import JobWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.main")

# Global instances for dependency injection
job_repository_instance: Optional[SQLiteJobRepository] = None
job_worker_instance: Optional[JobWorker] = None
video_service_instance: Optional[VideoService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context managing database connection and worker queue."""
    global job_repository_instance, job_worker_instance, video_service_instance

    logger.info("Initializing application infrastructure...")
    settings.ensure_directories()

    # Initialize repository
    job_repository_instance = SQLiteJobRepository(db_path=settings.DATABASE_PATH)
    await job_repository_instance.initialize()

    # Initialize background worker and service
    job_worker_instance = JobWorker(
        repo=job_repository_instance,
        max_concurrent=settings.MAX_CONCURRENT_JOBS,
    )
    video_service_instance = VideoService(
        repo=job_repository_instance,
        worker=job_worker_instance,
    )

    # Start worker tasks
    await job_worker_instance.start()
    logger.info("System initialized and ready to accept requests.")

    yield

    # Shutdown
    logger.info("Shutting down worker queue and terminating tasks...")
    if job_worker_instance:
        await job_worker_instance.stop()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Asynchronous backend service for generating educational chemistry videos with quality-gated fallback protection.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for browser API clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Top-level convenient health alias
app.add_api_route("/health", health_check, methods=["GET"], tags=["System"])
