"""Asynchronous background worker queue for processing video generation jobs."""

import asyncio
import logging
from typing import List, Optional

from app.core.config import settings
from app.models.job import JobStatus
from app.pipeline.pipeline import GenerationPipeline
from app.repositories.base import JobRepository

logger = logging.getLogger(__name__)


class JobWorker:
    """In-memory asyncio worker queue processing video requests with state persistence."""

    def __init__(
        self,
        repo: JobRepository,
        pipeline: Optional[GenerationPipeline] = None,
        max_concurrent: int = settings.MAX_CONCURRENT_JOBS,
    ) -> None:
        self.repo = repo
        self.pipeline = pipeline or GenerationPipeline()
        self.max_concurrent = max_concurrent
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.tasks: List[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        """Start background worker tasks."""
        if self._running:
            return
        self._running = True
        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker_loop(i))
            self.tasks.append(task)
        logger.info("JobWorker started with %d concurrent tasks", self.max_concurrent)

    async def stop(self) -> None:
        """Gracefully stop background worker tasks."""
        if not self._running:
            return
        self._running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        logger.info("JobWorker stopped successfully")

    async def enqueue(self, job_id: str) -> None:
        """Enqueue a job ID for processing."""
        await self.queue.put(job_id)
        logger.info("Enqueued job %s to worker queue (queue size: %d)", job_id, self.queue.qsize())

    async def _worker_loop(self, worker_index: int) -> None:
        """Individual worker task consuming jobs from the queue."""
        logger.debug("Worker task %d online", worker_index)
        while self._running:
            try:
                job_id = await self.queue.get()
            except asyncio.CancelledError:
                break

            try:
                logger.info("Worker %d starting execution for job %s", worker_index, job_id)
                await self._process_job(job_id)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Unexpected error processing job %s: %s", job_id, exc)
            finally:
                self.queue.task_done()

    async def _process_job(self, job_id: str) -> None:
        """Execute the video generation pipeline for a job and persist state transitions."""
        job = await self.repo.get_by_id(job_id)
        if not job:
            logger.error("Job %s not found in repository; aborting processing", job_id)
            return

        async def on_progress(status: JobStatus, pct: int, step: str) -> None:
            await self.repo.update_status(
                job_id=job_id,
                status=status,
                progress_pct=pct,
                current_step=step,
            )

        try:
            result = await self.pipeline.run(
                job_id=job.id,
                query=job.query,
                on_progress=on_progress,
            )

            # Mark job complete with artifact paths and metadata
            await self.repo.mark_completed(
                job_id=job_id,
                video_path=str(result.video_path),
                video_duration_seconds=result.duration_seconds,
                metadata=result.metadata,
            )
            logger.info("Job %s successfully completed (%0.2fs)", job_id, result.duration_seconds)

        except Exception as exc:
            logger.exception("Job %s generation failed: %s", job_id, exc)
            await self.repo.mark_failed(
                job_id=job_id,
                error_detail=str(exc),
            )
