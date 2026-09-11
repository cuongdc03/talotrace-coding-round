"""API endpoints for chemistry video generation jobs."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.models.job import Job, JobCreateRequest, JobListResponse, JobResponse, JobStatus
from app.services.video_service import VideoService

router = APIRouter()


def _job_to_response(job: Job) -> JobResponse:
    """Helper to convert domain Job to API JobResponse."""
    video_url = f"/api/v1/videos/jobs/{job.id}/video" if job.status == JobStatus.COMPLETED else None
    return JobResponse(
        id=job.id,
        query=job.query,
        topic=job.topic,
        status=job.status,
        progress_pct=job.progress_pct,
        current_step=job.current_step,
        error_detail=job.error_detail,
        video_url=video_url,
        video_duration_seconds=job.video_duration_seconds,
        metadata=job.metadata,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
    )


def get_video_service() -> VideoService:
    """Dependency provider for VideoService with on-demand fallback initialization."""
    import app.main as main_mod
    from app.core.config import settings
    from app.repositories.sqlite_job_repository import SQLiteJobRepository
    from app.services.worker import JobWorker

    if main_mod.video_service_instance is None:
        if main_mod.job_repository_instance is None:
            main_mod.job_repository_instance = SQLiteJobRepository(db_path=settings.DATABASE_PATH)
        if main_mod.job_worker_instance is None:
            main_mod.job_worker_instance = JobWorker(
                repo=main_mod.job_repository_instance,
                max_concurrent=settings.MAX_CONCURRENT_JOBS,
            )
        main_mod.video_service_instance = VideoService(
            repo=main_mod.job_repository_instance,
            worker=main_mod.job_worker_instance,
        )
    return main_mod.video_service_instance


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a new chemistry explanation video",
    description="Submits a learner query for asynchronous video generation.",
)
async def request_video_job(
    payload: JobCreateRequest,
    service: VideoService = Depends(get_video_service),
) -> JobResponse:
    """Submit a chemistry concept explanation video request."""
    job = await service.create_job(payload.query)
    return _job_to_response(job)


@router.get(
    "/jobs",
    response_model=JobListResponse,
    status_code=status.HTTP_200_OK,
    summary="List requested video jobs",
    description="Retrieve requested video jobs with optional status filter and pagination.",
)
async def list_video_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter jobs by status"),
    limit: int = Query(50, ge=1, le=100, description="Max jobs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: VideoService = Depends(get_video_service),
) -> JobListResponse:
    """List video generation jobs with pagination."""
    jobs, total = await service.list_jobs(status=status, limit=limit, offset=offset)
    return JobListResponse(
        total=total,
        limit=limit,
        offset=offset,
        jobs=[_job_to_response(j) for j in jobs],
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job status and metadata",
    description="Retrieve live progress and status for a specific video generation job.",
)
async def get_video_job(
    job_id: str,
    service: VideoService = Depends(get_video_service),
) -> JobResponse:
    """Fetch status for a specific video generation job."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )
    return _job_to_response(job)


@router.get(
    "/jobs/{job_id}/video",
    summary="Stream or download completed video artifact",
    description="Streams the generated .mp4 video explanation for completed jobs.",
)
async def get_video_artifact(
    job_id: str,
    service: VideoService = Depends(get_video_service),
):
    """Stream or download the completed video artifact."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    if job.status == JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job '{job_id}' failed generation: {job.error_detail}",
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job '{job_id}' is still in progress (status: {job.status.value}, {job.progress_pct}%)",
        )

    video_path = await service.get_video_file_path(job_id)
    if not video_path or not video_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video artifact for job '{job_id}' was not found on disk",
        )

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"{job_id}.mp4",
    )
