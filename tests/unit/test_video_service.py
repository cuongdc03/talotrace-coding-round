"""Unit tests for video service and worker queue."""

import asyncio
from pathlib import Path

import pytest

from app.models.job import JobStatus
from app.repositories.sqlite_job_repository import SQLiteJobRepository
from app.services.video_service import VideoService
from app.services.worker import JobWorker


@pytest.mark.asyncio
async def test_create_and_process_job(tmp_path: Path):
    db_path = tmp_path / "test_service.db"
    repo = SQLiteJobRepository(db_path=db_path)
    await repo.initialize()

    worker = JobWorker(repo=repo, max_concurrent=1)
    service = VideoService(repo=repo, worker=worker)

    # Start worker in background
    await worker.start()

    try:
        job = await service.create_job("How does the pH scale work?")
        assert job.id.startswith("job_")
        assert job.status == JobStatus.PENDING
        assert job.topic == "PH_SCALE"

        # Wait for worker to finish processing (poll for up to 30s)
        for _ in range(60):
            current = await service.get_job(job.id)
            if current and current.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
            await asyncio.sleep(0.5)

        final_job = await service.get_job(job.id)
        assert final_job is not None
        assert final_job.status == JobStatus.COMPLETED
        assert final_job.progress_pct == 100
        assert final_job.video_path is not None
        assert Path(final_job.video_path).exists()
        assert final_job.video_duration_seconds > 1.0

    finally:
        await worker.stop()


@pytest.mark.asyncio
async def test_job_service_metrics(tmp_path: Path):
    db_path = tmp_path / "test_metrics.db"
    repo = SQLiteJobRepository(db_path=db_path)
    await repo.initialize()

    worker = JobWorker(repo=repo, max_concurrent=1)
    service = VideoService(repo=repo, worker=worker)

    metrics = await service.get_metrics()
    assert metrics["total_jobs"] == 0
    assert metrics["completed_jobs"] == 0
