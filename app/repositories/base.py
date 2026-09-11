"""Abstract base repository for job persistence."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from app.models.job import Job, JobStatus


class JobRepository(ABC):
    """Abstract interface for video generation job persistence."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database tables and indexes."""
        pass

    @abstractmethod
    async def create(self, job: Job) -> Job:
        """Persist a new job record."""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by its unique ID."""
        pass

    @abstractmethod
    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        progress_pct: int,
        current_step: str,
    ) -> Job:
        """Update job lifecycle state, progress, and status message."""
        pass

    @abstractmethod
    async def mark_completed(
        self,
        job_id: str,
        video_path: str,
        video_duration_seconds: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """Mark a job as successfully completed with artifact details."""
        pass

    @abstractmethod
    async def mark_failed(
        self,
        job_id: str,
        error_detail: str,
    ) -> Job:
        """Mark a job as failed with an error message."""
        pass

    @abstractmethod
    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Job], int]:
        """List jobs with optional status filter and pagination. Returns (items, total_count)."""
        pass
