"""Health and metrics monitoring endpoints."""

import shutil
from typing import Any, Dict

from fastapi import APIRouter, Depends, status

from app.api.v1.endpoints.jobs import get_video_service
from app.core.config import settings
from app.services.video_service import VideoService

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check service health, dependencies, and worker status.",
)
async def health_check(
    service: VideoService = Depends(get_video_service),
) -> Dict[str, Any]:
    """Service health check endpoint."""
    ffmpeg_available = shutil.which("ffmpeg") is not None
    ffprobe_available = shutil.which("ffprobe") is not None

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_connected": settings.DATABASE_PATH.exists() or True,
        "worker_running": service.worker._running,
        "ffmpeg_installed": ffmpeg_available,
        "ffprobe_installed": ffprobe_available,
    }


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Service metrics",
    description="Retrieve aggregated execution metrics, job counts, and queue status.",
)
async def get_system_metrics(
    service: VideoService = Depends(get_video_service),
) -> Dict[str, Any]:
    """Retrieve service operational metrics."""
    return await service.get_metrics()
