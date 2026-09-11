"""Unit tests for asynchronous SQLite job repository."""

import pytest

from app.models.job import Job, JobStatus
from app.repositories.sqlite_job_repository import SQLiteJobRepository


@pytest.mark.asyncio
async def test_create_and_get_job(tmp_path):
    db_path = tmp_path / "test_jobs.db"
    repo = SQLiteJobRepository(db_path=db_path)
    await repo.initialize()

    job = Job(
        id="job_test_123",
        query="How does the pH scale work?",
        topic="PH_SCALE",
        status=JobStatus.PENDING,
        progress_pct=0,
        current_step="Job enqueued",
    )

    created = await repo.create(job)
    assert created.id == "job_test_123"

    retrieved = await repo.get_by_id("job_test_123")
    assert retrieved is not None
    assert retrieved.id == "job_test_123"
    assert retrieved.query == "How does the pH scale work?"
    assert retrieved.status == JobStatus.PENDING
    assert retrieved.progress_pct == 0
    assert retrieved.current_step == "Job enqueued"


@pytest.mark.asyncio
async def test_update_job_status_and_progress(tmp_path):
    db_path = tmp_path / "test_jobs.db"
    repo = SQLiteJobRepository(db_path=db_path)
    await repo.initialize()

    job = Job(
        id="job_test_update",
        query="Why do atoms form covalent bonds?",
        topic="COVALENT_BONDS",
        status=JobStatus.PENDING,
        progress_pct=0,
        current_step="Enqueued",
    )
    await repo.create(job)

    updated = await repo.update_status(
        job_id="job_test_update",
        status=JobStatus.RENDERING_VIDEO,
        progress_pct=75,
        current_step="Assembling MP4 video with FFmpeg",
    )
    assert updated.status == JobStatus.RENDERING_VIDEO
    assert updated.progress_pct == 75
    assert updated.current_step == "Assembling MP4 video with FFmpeg"

    retrieved = await repo.get_by_id("job_test_update")
    assert retrieved.status == JobStatus.RENDERING_VIDEO
    assert retrieved.progress_pct == 75


@pytest.mark.asyncio
async def test_complete_and_fail_job(tmp_path):
    db_path = tmp_path / "test_jobs.db"
    repo = SQLiteJobRepository(db_path=db_path)
    await repo.initialize()

    job1 = Job(
        id="job_test_complete",
        query="Query 1",
        topic="PH_SCALE",
        status=JobStatus.PENDING,
    )
    await repo.create(job1)

    completed = await repo.mark_completed(
        job_id="job_test_complete",
        video_path="artifacts/videos/ph_scale.mp4",
        video_duration_seconds=18.5,
        metadata={"scenes_count": 3, "cost_estimate": 0.0},
    )
    assert completed.status == JobStatus.COMPLETED
    assert completed.progress_pct == 100
    assert completed.video_path == "artifacts/videos/ph_scale.mp4"
    assert completed.video_duration_seconds == 18.5
    assert completed.completed_at is not None

    job2 = Job(
        id="job_test_fail",
        query="Invalid query",
        topic="UNKNOWN",
        status=JobStatus.PENDING,
    )
    await repo.create(job2)

    failed = await repo.mark_failed(
        job_id="job_test_fail",
        error_detail="Topic unsupported: quantum chromodynamics",
    )
    assert failed.status == JobStatus.FAILED
    assert failed.error_detail == "Topic unsupported: quantum chromodynamics"


@pytest.mark.asyncio
async def test_list_jobs_with_pagination_and_filter(tmp_path):
    db_path = tmp_path / "test_jobs.db"
    repo = SQLiteJobRepository(db_path=db_path)
    await repo.initialize()

    for i in range(5):
        await repo.create(
            Job(
                id=f"job_{i}",
                query=f"Query {i}",
                topic="PH_SCALE",
                status=JobStatus.COMPLETED if i % 2 == 0 else JobStatus.PENDING,
            )
        )

    all_jobs, total = await repo.list_jobs(limit=10, offset=0)
    assert total == 5
    assert len(all_jobs) == 5

    completed_jobs, total_completed = await repo.list_jobs(
        status=JobStatus.COMPLETED, limit=10, offset=0
    )
    assert total_completed == 3
    assert len(completed_jobs) == 3

    paged_jobs, _ = await repo.list_jobs(limit=2, offset=0)
    assert len(paged_jobs) == 2


@pytest.mark.asyncio
async def test_get_nonexistent_job_returns_none(tmp_path):
    db_path = tmp_path / "test_jobs.db"
    repo = SQLiteJobRepository(db_path=db_path)
    await repo.initialize()

    result = await repo.get_by_id("nonexistent_id")
    assert result is None
