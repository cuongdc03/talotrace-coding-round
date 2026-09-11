"""Script and storyboard domain models with schema guardrails."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SupportedTopic(str, Enum):
    """Canonical supported science topics."""

    PH_SCALE = "PH_SCALE"
    COVALENT_BONDS = "COVALENT_BONDS"
    IONIC_VS_COVALENT = "IONIC_VS_COVALENT"
    OTHER_STEM = "OTHER_STEM"


class Scene(BaseModel):
    """A discrete pedagogical scene in an educational video explanation."""

    scene_id: int = Field(..., ge=1, description="Sequential scene index (1-based)")
    title: str = Field(..., min_length=2, max_length=100, description="Scene title header")
    narration: str = Field(
        ..., min_length=10, max_length=500, description="Spoken voiceover narration"
    )
    visual_type: str = Field(
        ..., min_length=3, max_length=50, description="Visual scene template identifier"
    )
    key_takeaway: str = Field(
        ..., min_length=3, max_length=150, description="On-screen bullet / takeaway"
    )
    duration_target_seconds: Optional[float] = Field(default=5.0, ge=1.0, le=60.0)


class VideoScript(BaseModel):
    """Validated multi-scene storyboard script for video generation."""

    topic: SupportedTopic = Field(..., description="Canonical topic category")
    title: str = Field(..., min_length=5, max_length=120, description="Overall video title")
    overview: str = Field(
        ..., min_length=10, max_length=300, description="Brief educational summary"
    )
    scenes: List[Scene] = Field(
        ..., min_length=2, max_length=10, description="Ordered list of scenes"
    )
