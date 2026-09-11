"""Asynchronous SQLite implementation of the JobRepository."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

from app.models.job import Job, JobStatus
from app.repositories.base import JobRepository


class SQLiteJobRepository(JobRepository):
    """Async SQLite persistence repository for jobs."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Create database tables and indexes if they do not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_pct INTEGER NOT NULL DEFAULT 0,
                    current_step TEXT NOT NULL,
                    error_detail TEXT,
                    video_path TEXT,
                    video_duration_seconds REAL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )
            await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)"
            )
            await db.commit()

    def _row_to_job(self, row: aiosqlite.Row) -> Job:
        """Convert a database row into a Job domain model."""
        return Job(
            id=row["id"],
            query=row["query"],
            topic=row["topic"],
            status=JobStatus(row["status"]),
            progress_pct=row["progress_pct"],
            current_step=row["current_step"],
            error_detail=row["error_detail"],
            video_path=row["video_path"],
            video_duration_seconds=row["video_duration_seconds"],
            metadata=json.loads(row["metadata_json"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
        )

    async def create(self, job: Job) -> Job:
        """Persist a new job record."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO jobs (
                    id, query, topic, status, progress_pct, current_step,
                    error_detail, video_path, video_duration_seconds,
                    metadata_json, created_at, updated_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.query,
                    job.topic,
                    job.status.value,
                    job.progress_pct,
                    job.current_step,
                    job.error_detail,
                    job.video_path,
                    job.video_duration_seconds,
                    json.dumps(job.metadata),
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    job.completed_at.isoformat() if job.completed_at else None,
                ),
            )
            await db.commit()
        return job

    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by its unique ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return self._row_to_job(row)

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        progress_pct: int,
        current_step: str,
    ) -> Job:
        """Update job lifecycle state, progress, and status message."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs
                SET status = ?, progress_pct = ?, current_step = ?, updated_at = ?
                WHERE id = ?
                """,
                (status.value, progress_pct, current_step, now, job_id),
            )
            await db.commit()
        job = await self.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found for status update")
        return job

    async def mark_completed(
        self,
        job_id: str,
        video_path: str,
        video_duration_seconds: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """Mark a job as successfully completed with artifact details."""
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.isoformat()
        existing = await self.get_by_id(job_id)
        if not existing:
            raise ValueError(f"Job {job_id} not found")

        merged_metadata = {**existing.metadata, **(metadata or {})}
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs
                SET status = ?, progress_pct = 100, current_step = 'Completed',
                    video_path = ?, video_duration_seconds = ?, metadata_json = ?,
                    updated_at = ?, completed_at = ?
                WHERE id = ?
                """,
                (
                    JobStatus.COMPLETED.value,
                    video_path,
                    video_duration_seconds,
                    json.dumps(merged_metadata),
                    now_str,
                    now_str,
                    job_id,
                ),
            )
            await db.commit()
        return await self.get_by_id(job_id)

    async def mark_failed(
        self,
        job_id: str,
        error_detail: str,
    ) -> Job:
        """Mark a job as failed with an error message."""
        now_str = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs
                SET status = ?, current_step = 'Failed', error_detail = ?, updated_at = ?
                WHERE id = ?
                """,
                (JobStatus.FAILED.value, error_detail, now_str, job_id),
            )
            await db.commit()
        return await self.get_by_id(job_id)

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Job], int]:
        """List jobs with optional status filter and pagination. Returns (items, total_count)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                count_query = "SELECT COUNT(*) FROM jobs WHERE status = ?"
                count_params = (status.value,)
                select_query = (
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
                )
                select_params = (status.value, limit, offset)
            else:
                count_query = "SELECT COUNT(*) FROM jobs"
                count_params = ()
                select_query = "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?"
                select_params = (limit, offset)

            async with db.execute(count_query, count_params) as cursor:
                row = await cursor.fetchone()
                total = row[0] if row else 0

            async with db.execute(select_query, select_params) as cursor:
                rows = await cursor.fetchall()
                jobs = [self._row_to_job(r) for r in rows]

            return jobs, total
