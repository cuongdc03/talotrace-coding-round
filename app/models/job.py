"""Job domain models and schema definitions."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Lifecycle status states for video generation jobs."""

    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    GENERATING_SCRIPT = "GENERATING_SCRIPT"
    SYNTHESIZING_AUDIO = "SYNTHESIZING_AUDIO"
    RENDERING_VIDEO = "RENDERING_VIDEO"
    VERIFYING_ARTIFACT = "VERIFYING_ARTIFACT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Job(BaseModel):
    """Domain model representing a video generation request and lifecycle state."""

    id: str
    query: str
    topic: str
    status: JobStatus = JobStatus.PENDING
    progress_pct: int = Field(default=0, ge=0, le=100)
    current_step: str = "Job created"
    error_detail: Optional[str] = None
    video_path: Optional[str] = None
    video_duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class JobCreateRequest(BaseModel):
    """HTTP request payload for requesting a new concept explanation video."""

    query: str = Field(..., min_length=3, max_length=500, description="Learner chemistry query")


class JobResponse(BaseModel):
    """Detailed job state response model."""

    id: str
    query: str
    topic: str
    status: JobStatus
    progress_pct: int
    current_step: str
    error_detail: Optional[str] = None
    video_url: Optional[str] = None
    video_duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class JobListResponse(BaseModel):
    """Paginated list of jobs response model."""

    total: int
    limit: int
    offset: int
    jobs: List[JobResponse]
