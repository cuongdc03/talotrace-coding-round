"""Video request service coordinating jobs, worker queue, and artifacts."""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.models.job import Job, JobStatus
from app.pipeline.classifier import ConceptClassifier
from app.repositories.base import JobRepository
from app.services.worker import JobWorker

logger = logging.getLogger(__name__)


class VideoService:
    """Service layer orchestrating video requests, job states, and artifact serving."""

    def __init__(
        self,
        repo: JobRepository,
        worker: JobWorker,
        classifier: Optional[ConceptClassifier] = None,
    ) -> None:
        self.repo = repo
        self.worker = worker
        self.classifier = classifier or ConceptClassifier()

    async def create_job(self, query: str) -> Job:
        """Validate, persist, and enqueue a new video generation request."""
        topic = self.classifier.classify(query)
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        job = Job(
            id=job_id,
            query=query.strip(),
            topic=topic.value,
            status=JobStatus.PENDING,
            progress_pct=0,
            current_step="Job accepted and enqueued",
        )

        created_job = await self.repo.create(job)
        await self.worker.enqueue(created_job.id)
        logger.info("Created and enqueued job %s for topic %s", created_job.id, topic.value)
        return created_job

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Fetch job status and metadata by ID."""
        return await self.repo.get_by_id(job_id)

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Job], int]:
        """List jobs with pagination and optional status filter."""
        return await self.repo.list_jobs(status=status, limit=limit, offset=offset)

    async def get_video_file_path(self, job_id: str) -> Optional[Path]:
        """Retrieve local path to completed video file if available and verified."""
        job = await self.repo.get_by_id(job_id)
        if not job or job.status != JobStatus.COMPLETED or not job.video_path:
            return None

        path = Path(job.video_path)
        if path.exists() and path.stat().st_size > 0:
            return path
        return None

    async def get_metrics(self) -> Dict[str, Any]:
        """Aggregate system execution metrics and worker health."""
        all_jobs, total = await self.repo.list_jobs(limit=1000, offset=0)
        completed = sum(1 for j in all_jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in all_jobs if j.status == JobStatus.FAILED)
        active = sum(
            1
            for j in all_jobs
            if j.status
            in [
                JobStatus.PENDING,
                JobStatus.VALIDATING,
                JobStatus.GENERATING_SCRIPT,
                JobStatus.SYNTHESIZING_AUDIO,
                JobStatus.RENDERING_VIDEO,
                JobStatus.VERIFYING_ARTIFACT,
            ]
        )

        total_duration = sum(
            j.video_duration_seconds or 0.0 for j in all_jobs if j.video_duration_seconds
        )
        avg_duration = round(total_duration / completed, 2) if completed > 0 else 0.0

        return {
            "total_jobs": total,
            "completed_jobs": completed,
            "failed_jobs": failed,
            "active_jobs": active,
            "average_video_duration_seconds": avg_duration,
            "queue_size": self.worker.queue.qsize(),
            "worker_running": self.worker._running,
        }
